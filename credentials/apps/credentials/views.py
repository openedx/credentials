import datetime
import logging
import uuid

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from credentials.apps.core.views import ThemeViewMixin
from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import OrganizationDetails, ProgramCertificate, ProgramDetails, UserCredential
from credentials.apps.credentials.utils import get_credential_visible_date, to_language


logger = logging.getLogger(__name__)


class SocialMediaMixin:
    """ Mixin with context for sharing certificates to social media networks. """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        site_configuration = request.site.siteconfiguration
        context.update({
            'facebook_app_id': site_configuration.facebook_app_id,
            'twitter_username': site_configuration.twitter_username,
            'enable_facebook_sharing': site_configuration.enable_facebook_sharing,
            'enable_linkedin_sharing': site_configuration.enable_linkedin_sharing,
            'enable_twitter_sharing': site_configuration.enable_twitter_sharing,
            'share_url': request.build_absolute_uri,
            'tweet_text': _('I completed a course at {platform_name}. Take a look at my certificate:').format(
                platform_name=site_configuration.platform_name),
        })
        return context


class RenderCredential(SocialMediaMixin, ThemeViewMixin, TemplateView):
    """ Certificate rendering view."""
    # This base template will include a separate template housing the requested credential body.
    # This allows us to use this one view to render credentials for any number of content types
    # (e.g., courses, programs).
    template_name = 'credentials/base.html'

    @cached_property
    def user_credential(self):
        return get_object_or_404(
            UserCredential,
            uuid=self.kwargs.get('uuid'),
            status=UserCredential.AWARDED,
            program_credentials__site=self.request.site,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_credential = self.user_credential
        organization_names = []

        # NOTE: We currently only support rendering program credentials
        if user_credential.credential_content_type.model_class() != ProgramCertificate:
            raise Http404

        visible_date = get_credential_visible_date(user_credential)
        now = datetime.datetime.now(datetime.timezone.utc)
        if now < visible_date:
            raise Http404

        program_details = user_credential.credential.program_details
        for organization in program_details.organizations:
            organization_names.append(organization.display_name)
            if not organization.certificate_logo_image_url:
                raise MissingCertificateLogoError('No certificate image logo defined for program: [{program_uuid}]'.
                                                  format(program_uuid=program_details.uuid))

        org_name_string = ""
        if len(organization_names) == 1:
            org_name_string = organization_names[0]
        elif len(organization_names) == 2:
            org_name_string = _('{first_org} and {second_org}').format(first_org=organization_names[0],
                                                                       second_org=organization_names[1])
        elif organization_names:
            org_name_string = _("{series_of_orgs}, and {last_org}").format(
                series_of_orgs=', '.join(organization_names[:-1]), last_org=organization_names[-1])

        user_data = user_credential.credential.site.siteconfiguration.get_user_api_data(user_credential.username)
        content_language = to_language(user_credential.credential.language)

        context.update({
            'user_credential': user_credential,
            'user_data': user_data,
            'child_templates': self.get_child_templates(),
            'render_language': content_language if content_language else settings.LANGUAGE_CODE,
            'issue_date': visible_date,

            # NOTE: In the future this can be set to the course_name and/or seat type
            'page_title': program_details.type,

            # NOTE: In the future this can be set to the course_name
            'program_name': program_details.title,
            'credential_title': program_details.credential_title,
            'org_name_string': org_name_string,
        })
        if program_details.hours_of_effort:
            context.update({'hours_of_effort': program_details.hours_of_effort})

        return context

    def get_credential_template(self):
        template_names = []
        credential_type = self.user_credential.credential

        # NOTE: In the future we will need to account for other types of credentials besides programs.
        template_names += [
            f'credentials/programs/{credential_type.program_uuid}/certificate.html',
            'credentials/programs/{type}/certificate.html'.format(
                type=slugify(credential_type.program_details.type)),
        ]

        return self.select_theme_template(template_names)

    def get_child_templates(self):
        return {
            'credential': self.get_credential_template(),
            'footer': self.select_theme_template(['_footer.html']),
            'header': self.select_theme_template(['_header.html']),
        }


class ExampleCredential(SocialMediaMixin, ThemeViewMixin, TemplateView):
    """ Example certificate. """
    template_name = 'credentials/base.html'

    def get_context_data(self, **kwargs):
        program_type = self.request.GET.get('program_type', 'Professional Certificate')
        context = super().get_context_data(**kwargs)
        program_details = ProgramDetails(
            uuid=uuid.uuid4(),
            title='Completely Example Program',
            subtitle='Example Subtitle',
            type=program_type,
            credential_title=None,
            course_count=3,
            organizations=[OrganizationDetails(
                uuid=uuid.uuid4(),
                key='ExampleX',
                name='Example University',
                display_name='Absolutely Fake University',
                certificate_logo_image_url='https://placehold.it/204x204'
            )],
            hours_of_effort=None
        )

        context.update({
            'user_credential': {
                'modified': timezone.now(),
                'uuid': uuid.uuid4(),
                'credential': {
                    'program_uuid': uuid.uuid4(),
                    'signatories': {
                        # NOTE (CCB): This is a small hack to workaround the fact that the template expects a QuerySet.
                        'all': [
                            {
                                'name': 'Pseudo McFakerson',
                                'title': 'Professor...really just Some Guy',
                                'organization_name_override': 'Parts Unknown',
                                'image': {
                                    'url': 'https://placehold.it/720x280'
                                }
                            }
                        ]
                    },
                    'program_details': program_details,
                },
            },
            'user_data': {
                'name': 'John Doe',
                'username': self.request.user.username,
            },
            'child_templates': {
                'credential': self.select_theme_template(
                    ['credentials/programs/{type}/certificate.html'.format(type=slugify(program_type))]),
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
            'page_title': program_details.type,
            'program_name': program_details.title,
            'credential_title': program_details.credential_title,
            'render_language': settings.LANGUAGE_CODE,
            'org_name_string': 'Example University',
        })

        return context
