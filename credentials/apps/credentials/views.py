"""
Credentials rendering views.
"""
import logging

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from credentials.apps.credentials.models import UserCredential, ProgramCertificate
from credentials.apps.credentials.utils import get_organization, get_program


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
            'certificate_context': self.get_program_certificate_context(user_credential),
        })

        return context

    def get_program_certificate_context(self, user_credential):
        """ Get the program certificate related data from database.

        Arguments:
            user_credential (User): UserCredential object

        Returns:
             dict, representing a data returned by the Program service,
             lms service and template path.
        """
        programs_data = self._get_program_data(user_credential.credential.program_id)
        return {
            'programs_data': programs_data,
            'organization_data': get_organization(programs_data['organization_key']),
            'credential_template': 'credentials/program_certificate.html'
        }

    def _get_program_data(self, program_id):
        """ Get the program data from program service.

        Arguments:
            program_id (int): Unique id of the program for retrieval

        Returns:
            dict, representing a parsed program data returned by the Program service.
        """
        program_data = get_program(program_id)
        return {
            'course_count': len(program_data['course_codes']),
            'organization_key': program_data['organizations'][0]['key'],
            'category': program_data['category'],
        }
