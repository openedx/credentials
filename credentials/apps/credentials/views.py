import logging
import uuid

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.template.loader import select_template
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import OrganizationDetails, ProgramCertificate, ProgramDetails, UserCredential

logger = logging.getLogger(__name__)


class SocialMediaMixin:
    """ Mixin with context for sharing certificates to social media networks. """

    def get_context_data(self, **kwargs):
        context = super(SocialMediaMixin, self).get_context_data(**kwargs)
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


class ThemeViewMixin:
    site = None

    def add_theme_to_template_names(self, template_names):
        """ Prepend the the list of template names with the path of the current theme. """
        theme_template_path = self.site.siteconfiguration.theme_name
        themed_template_names = [
            '{theme_path}/{template_name}'.format(theme_path=theme_template_path,
                                                  template_name=template_name.strip('/')) for
            template_name in template_names
        ]
        template_names = themed_template_names + template_names
        return template_names

    def select_theme_template(self, templates):
        return select_template(self.add_theme_to_template_names(templates))


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
            status=UserCredential.AWARDED
        )

    def get_context_data(self, **kwargs):
        context = super(RenderCredential, self).get_context_data(**kwargs)
        user_credential = self.user_credential

        # NOTE: We currently only support rendering program credentials
        if user_credential.credential_content_type.model_class() != ProgramCertificate:
            raise Http404

        program_details = user_credential.credential.program_details
        for organization in program_details.organizations:
            if not organization.certificate_logo_image_url:
                raise MissingCertificateLogoError('No certificate image logo defined for program: [{program_uuid}]'.
                                                  format(program_uuid=program_details.uuid))

        self.site = user_credential.credential.site
        user_data = self.site.siteconfiguration.get_user_api_data(user_credential.username)

        context.update({
            'user_credential': user_credential,
            'user_data': user_data,
            'child_templates': self.get_child_templates(),

            # NOTE: In the future this can be set to the course_name and/or seat type
            'page_title': program_details.type,

            # NOTE: In the future this can be set to the course_name
            'program_name': program_details.title,
        })

        return context

    def get_credential_template(self):
        template_names = []
        credential_type = self.user_credential.credential

        # NOTE: In the future we will need to account for other types of credentials besides programs.
        template_names += [
            'credentials/programs/{uuid}/certificate.html'.format(uuid=credential_type.program_uuid),
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
        context = super(ExampleCredential, self).get_context_data(**kwargs)
        program_details = ProgramDetails(
            uuid=uuid.uuid4(),
            title='Completely Example Program',
            type=program_type,
            course_count=3,
            organizations=[OrganizationDetails(
                uuid=uuid.uuid4(),
                key='ExampleX',
                name='Example University',
                display_name='Absolutely Fake University',
                certificate_logo_image_url='https://placehold.it/204x204'
            )]
        )

        self.site = self.request.site

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
            },
            'child_templates': {
                'credential': self.select_theme_template(
                    ['credentials/programs/{type}/certificate.html'.format(type=slugify(program_type))]),
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
        })

        return context
