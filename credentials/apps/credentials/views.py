from __future__ import unicode_literals

import logging
import uuid

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from credentials.apps.credentials.models import UserCredential, ProgramCertificate, ProgramDetails
from credentials.apps.credentials.utils import get_organization, get_user_data

logger = logging.getLogger(__name__)


class RenderCredential(TemplateView):
    """ Certificate rendering view."""
    template_name = 'credentials/render_credential.html'

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
        organization_data = get_organization(program_details.organization_keys[0])
        organization_name = organization_data['short_name']
        if user_credential.credential.use_org_name:
            organization_name = organization_data['name']

        # pylint: disable=no-member
        return {
            'credential_type': _('{program_type} Certificate').format(program_type=program_details.type),
            'credential_title': user_credential.credential.title,
            'user_data': get_user_data(user_credential.username),
            'program_details': program_details,
            'organization_data': organization_data,
            'organization_name': organization_name,
            'credential_template': 'credentials/program_certificate.html',
        }


class ExampleCredential(TemplateView):
    """ Example certificate. """
    template_name = 'credentials/render_credential.html'

    def get_context_data(self, **kwargs):
        context = super(ExampleCredential, self).get_context_data(**kwargs)
        context.update({
            'user_credential': {
                'modified': timezone.now(),
                'uuid': uuid.uuid4(),
                'credential': {
                    'signatories': [],
                }
            },
            'certificate_context': {
                'credential_type': 'Demo Certificate',
                'credential_title': 'Completely Example Program',
                'user_data': {
                    'name': 'John Doe',
                },
                'program_details': ProgramDetails(
                    uuid=uuid.uuid4(),
                    title='Completely Example Program',
                    type='Fake',
                    organization_keys=['ExampleX'],
                    course_count=3
                ),
                'organization_data': {
                    'short_name': 'ExampleX',
                    'name': 'Example University',
                    'logo': 'http://placehold.it/204x204',
                },
                'organization_name': 'Example, Inc.',
                'credential_template': 'credentials/program_certificate.html',
            },
        })

        return context
