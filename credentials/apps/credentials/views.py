from __future__ import unicode_literals

import logging
import uuid

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.views.generic import TemplateView

from credentials.apps.credentials.models import UserCredential, ProgramCertificate, ProgramDetails, OrganizationDetails
from credentials.apps.credentials.utils import get_user_data

logger = logging.getLogger(__name__)


class RenderCredential(TemplateView):
    """ Certificate rendering view."""
    # This base template will include a separate template housing the requested credential body.
    # This allows us to use this one view to render credentials for any number of content types
    # (e.g., courses, programs).
    template_name = 'credentials/base.html'

    def get_context_data(self, **kwargs):
        context = super(RenderCredential, self).get_context_data(**kwargs)
        user_credential = get_object_or_404(
            UserCredential,
            uuid=kwargs.get('uuid'),
            status=UserCredential.AWARDED
        )

        # get the model class according the credential content type.
        # It will be use to call the appropriate method for rendering.
        if user_credential.credential_content_type.model_class() != ProgramCertificate:
            raise Http404

        context.update({
            'user_credential': user_credential,
            'certificate_context': self.get_certificate_context(user_credential),
        })

        return context

    def get_certificate_context(self, user_credential):
        """ Returns the context data necessary to render the certificate.

        Arguments:
            user_credential (UserCredential): UserCredential being rendered

        Returns:
             dict, representing a data returned by the Program service,
             lms service and template path.
        """
        program_details = user_credential.credential.program_details
        program_type = program_details.type
        credential_template = 'credentials/programs/{}.html'.format(slugify(program_type))
        # pylint: disable=no-member
        return {
            'credential_type': program_type,
            'credential_title': user_credential.credential.title,
            'user_data': get_user_data(user_credential.username),
            'program_details': program_details,
            'credential_template': credential_template,
        }


class ExampleCredential(TemplateView):
    """ Example certificate. """
    template_name = 'credentials/base.html'

    def get_context_data(self, **kwargs):
        program_type = self.request.GET.get('program_type', 'Example')
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
                logo_image_url='http://placehold.it/204x204'
            )]
        )

        context.update({
            'user_credential': {
                'modified': timezone.now(),
                'uuid': uuid.uuid4(),
                'credential': {
                    'signatories': {
                        # NOTE (CCB): This is a small hack to workaround the fact that the template expects a QuerySet.
                        'all': [
                            {
                                'name': 'Pseudo McFakerson',
                                'title': 'Professor...really just Some Guy',
                                'organization_name_override': 'Parts Unknown',
                                'image': {
                                    'url': 'http://placehold.it/720x280'
                                }
                            }
                        ]
                    },
                }
            },
            'certificate_context': {
                'credential_type': 'Example Certificate',
                'credential_title': 'Completely Example Program',
                'user_data': {
                    'name': 'John Doe',
                },
                'program_details': program_details,
                'credential_template': 'credentials/programs/{}.html'.format(slugify(program_type)),
            },
        })

        return context
