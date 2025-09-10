import datetime
import logging
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext as _, override
from django.views.generic import TemplateView

from credentials.apps.catalog.data import OrganizationDetails, ProgramDetails
from credentials.apps.core.views import ThemeViewMixin
from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import ProgramCertificate, UserCredential
from credentials.apps.credentials.utils import get_credential_visible_date, to_language


logger = logging.getLogger(__name__)


class SocialMediaMixin:
    """Mixin with context for sharing certificates to social media networks."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        self.site_configuration = request.site.siteconfiguration
        context.update(
            {
                "enable_facebook_sharing": self.site_configuration.enable_facebook_sharing,
                "enable_linkedin_sharing": self.site_configuration.enable_linkedin_sharing,
                "enable_twitter_sharing": self.site_configuration.enable_twitter_sharing,
            }
        )
        return context


def _get_organizations_list(program_details):
    organization_names = []
    for organization in program_details.organizations:
        organization_names.append(organization.display_name)
        if not organization.certificate_logo_image_url:
            raise MissingCertificateLogoError(
                "No certificate image logo defined for program: [{program_uuid}]".format(
                    program_uuid=program_details.uuid
                )
            )
    return organization_names


def _get_org_name(organization_names, render_language):
    org_name_string = ""
    with override(render_language):
        if len(organization_names) == 1:
            org_name_string = organization_names[0]
        elif len(organization_names) == 2:
            org_name_string = _("{first_org} and {second_org}").format(
                first_org=organization_names[0], second_org=organization_names[1]
            )
        elif organization_names:
            org_name_string = _("{series_of_orgs}, and {last_org}").format(
                series_of_orgs=", ".join(organization_names[:-1]), last_org=organization_names[-1]
            )
    return org_name_string


class RenderCredential(SocialMediaMixin, ThemeViewMixin, TemplateView):
    """Certificate rendering view."""

    # This base template will include a separate template housing the requested credential body.
    # This allows us to use this one view to render credentials for any number of content types
    # (e.g., courses, programs).
    template_name = "credentials/base.html"

    @cached_property
    def user_credential(self):
        return get_object_or_404(
            UserCredential,
            uuid=self.kwargs.get("uuid"),
            status=UserCredential.AWARDED,
            program_credentials__site=self.request.site,
        )

    def get_visible_date(self):
        visible_date = get_credential_visible_date(self.user_credential)
        now = datetime.datetime.now(datetime.timezone.utc)
        if not visible_date or now < visible_date:
            raise Http404
        return visible_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_credential = self.user_credential

        # NOTE: We currently only support rendering program credentials
        if user_credential.credential_content_type.model_class() != ProgramCertificate:
            raise Http404

        visible_date = self.get_visible_date()

        program_details = user_credential.credential.program_details  # type: ProgramDetails
        organization_names = _get_organizations_list(program_details)

        content_language = to_language(user_credential.credential.language)
        render_language = content_language if content_language else settings.LANGUAGE_CODE

        org_name_string = _get_org_name(organization_names, render_language)

        user_data = user_credential.credential.site.siteconfiguration.get_user_api_data(user_credential.username)

        credential_name = user_data["name"]
        if user_data.get("use_verified_name_for_certs"):
            credential_name = user_data["verified_name"]

        # Twitter
        if self.site_configuration.enable_twitter_sharing:
            tweet_text = _("I completed a course at {platform_name}. Take a look at my certificate:").format(
                platform_name=self.site_configuration.platform_name
            )
            twitter_params = {
                "text": tweet_text,
                "url": self.request.build_absolute_uri(),
            }
            twitter_username = self.site_configuration.twitter_username or ""  # type: str
            if twitter_username:
                twitter_params["via"] = twitter_username
            twitter_url = "https://twitter.com/intent/tweet?{params}".format(params=urlencode(twitter_params))
            context.update(
                {
                    "twitter_url": twitter_url,
                }
            )

        # LinkedIn
        # See https://addtoprofile.linkedin.com/ for documentation on parameters
        # We don't populate the LinkedIn org ID in the catalog app, so use org name.
        if self.site_configuration.enable_linkedin_sharing:
            linkedin_params = {
                "name": program_details.credential_title or program_details.title,
                "certUrl": self.request.build_absolute_uri(),
                "certId": user_credential.uuid.hex,
                "organizationName": org_name_string,
                "issueYear": visible_date.year,
                "issueMonth": visible_date.month,
            }
            linkedin_url = "https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&{params}".format(
                params=urlencode(linkedin_params)
            )
            context.update(
                {
                    "linkedin_url": linkedin_url,
                }
            )

        # Facebook
        # See https://developers.facebook.com/docs/sharing/reference/share-dialog
        # for documentation on parameters.
        if self.site_configuration.enable_facebook_sharing:
            facebook_params = {
                "app_id": self.site_configuration.facebook_app_id,
                "display": "popup",
                "href": self.request.build_absolute_uri(),
            }
            facebook_url = "https://www.facebook.com/dialog/share?{params}".format(params=urlencode(facebook_params))
            context.update(
                {
                    "facebook_url": facebook_url,
                }
            )

        context.update(
            {
                "user_credential": user_credential,
                "user_data": user_data,
                "credential_name": credential_name,
                "child_templates": self.get_child_templates(),
                "render_language": render_language,
                "issue_date": visible_date,
                # NOTE: In the future this can be set to the course_name and/or seat type
                "page_title": program_details.type,
                # NOTE: In the future this can be set to the course_name
                "program_name": program_details.title,
                "credential_title": program_details.credential_title,
                "org_name_string": org_name_string,
                "share_url": self.request.build_absolute_uri(),
                "share_image_url": program_details.organizations[0].certificate_logo_image_url,
                "share_text": _("I completed a course at {platform_name}.").format(
                    platform_name=self.site_configuration.platform_name
                ),
            }
        )
        if program_details.hours_of_effort:
            context.update({"hours_of_effort": program_details.hours_of_effort})

        return context

    def get_credential_template(self):
        template_names = []
        credential_type = self.user_credential.credential

        # NOTE: In the future we will need to account for other types of credentials besides programs.
        template_names += [
            f"credentials/programs/{credential_type.program_uuid}/certificate.html",
            "credentials/programs/{type}/certificate.html".format(type=slugify(credential_type.program_details.type)),
        ]

        return self.select_theme_template(template_names)

    def get_child_templates(self):
        return {
            "credential": self.get_credential_template(),
            "footer": self.select_theme_template(["_footer.html"]),
            "header": self.select_theme_template(["_header.html"]),
        }


@method_decorator(staff_member_required(login_url=settings.LOGIN_URL), name="dispatch")
class RenderExampleProgramCredential(RenderCredential):
    """
    This View overrides just enough of the RenderCredential View to be able to display an example certificate.
    """

    @cached_property
    def user_credential(self):
        """
        We override this method to allow a preview of the program credential certificate without needing to also create
        UserCredentials.

        Returns:
        """
        program_cert = ProgramCertificate.objects.get(program__uuid=self.kwargs.get("uuid"))
        return UserCredential(
            pk=999999999,
            uuid=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            status=UserCredential.AWARDED,
            username=self.request.user.username,
            credential=program_cert,
            created=datetime.datetime.now(datetime.timezone.utc),
        )

    def get_visible_date(self):
        """
        We override this method to allow a preview of the program credential certificate without creating supporting
        course UserCredentials.
        """
        return datetime.datetime.now(datetime.timezone.utc)


class ExampleCredential(SocialMediaMixin, ThemeViewMixin, TemplateView):
    """Example certificate."""

    template_name = "credentials/base.html"

    def get_context_data(self, **kwargs):
        program_type = self.request.GET.get("program_type", "Professional Certificate")
        context = super().get_context_data(**kwargs)
        program_details = ProgramDetails(
            uuid=uuid.uuid4(),
            title="Completely Example Program",
            type=program_type,
            type_slug=slugify(program_type),
            credential_title=None,
            course_count=3,
            organizations=[
                OrganizationDetails(
                    uuid=uuid.uuid4(),
                    key="ExampleX",
                    name="Example University",
                    display_name="Absolutely Fake University",
                    certificate_logo_image_url="https://placehold.it/204x204",
                )
            ],
            hours_of_effort=None,
            status="active",
        )

        context.update(
            {
                "credential_name": "John Doe",
                "user_credential": {
                    "modified": timezone.now(),
                    "uuid": uuid.uuid4(),
                    "credential": {
                        "program_uuid": uuid.uuid4(),
                        "signatories": {
                            # NOTE (CCB): This is a small hack to workaround the fact that the template expects a
                            # QuerySet.
                            "all": [
                                {
                                    "name": "Pseudo McFakerson",
                                    "title": "Professor...really just Some Guy",
                                    "organization_name_override": "Parts Unknown",
                                    "image": {"url": "https://placehold.it/720x280"},
                                }
                            ]
                        },
                        "program_details": program_details,
                    },
                },
                "user_data": {
                    "name": "John Doe",
                    "username": self.request.user.username,
                },
                "child_templates": {
                    "credential": self.select_theme_template(
                        ["credentials/programs/{type}/certificate.html".format(type=slugify(program_type))]
                    ),
                    "footer": self.select_theme_template(["_footer.html"]),
                    "header": self.select_theme_template(["_header.html"]),
                },
                "page_title": program_details.type,
                "program_name": program_details.title,
                "credential_title": program_details.credential_title,
                "render_language": settings.LANGUAGE_CODE,
                "org_name_string": "Example University",
            }
        )

        return context
