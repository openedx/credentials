"""
Credentials rendering views.
"""
import logging

from django.conf import settings
from django.http import Http404
from django.template import Template, Context, loader
from django.utils import translation
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from credentials.apps.credentials.models import UserCredential, ProgramCertificate


logger = logging.getLogger(__name__)


class RenderCredential(TemplateView):
    """ Certificate rendering view."""
    template_name = 'credentials/render_credential.html'

    def get_context_data(self, **kwargs):
        context = super(RenderCredential, self).get_context_data(**kwargs)

        certificate_uuid = kwargs.get('uuid')
        try:
            user_credential = UserCredential.objects.get(uuid=certificate_uuid)
        except UserCredential.DoesNotExist:
            raise Http404

        # get the model class according the credential content type.
        generic_model = user_credential.credential_content_type.model_class()
        if generic_model == ProgramCertificate:
            try:
                program = ProgramCertificate.objects.get(pk=user_credential.credential_id)
            except ProgramCertificate.DoesNotExist:
                raise Http404

            signatories = program.signatories.all()
        else:
            # Only Programs credentials are supported.
            raise Http404

        # if program has a template in db then it will render otherwise uses
        # the default static template.
        if program.template:
            rendered_certificate = self.render_program_certificate(program, user_credential)
        else:
            rendered_certificate = self.render_default_template(user_credential, signatories)

        context.update({
            'rendered_certificate': rendered_certificate,
        })
        return context

    def render_program_certificate(self, program, user_credential):
        """ Render the template from database."""
        program_template = Template(program.template.content)
        context = Context({
            'content': program.template.content
        })
        context.update(self._update_certificate_context(user_credential))
        program_certificate_context = program_template.render(context)
        return program_certificate_context

    def render_default_template(self, credential, signatories):
        """ Render the static template."""
        program_template = loader.get_template('credentials/static/view_certificate.html')
        context = Context({
            'signatories': signatories,
        })
        context.update(self._update_certificate_context(credential))
        program_certificate_context = program_template.render(context)
        return program_certificate_context

    def _update_certificate_context(self, user_certificate):
        """
        Helper method to build up the certificate web view context using the
        provided values.
        """

        # Translators:  The format of the date includes the full name of the month.
        certificate_date_issued = _('{month} {day}, {year}').format(
            month=user_certificate.modified.strftime("%B"),
            day=user_certificate.modified.day,
            year=user_certificate.modified.year
        )
        # Translators: This text is bound to the HTML 'title' element of the page and appears in the browser title bar.
        document_title = _('{partner_short_name} {course_number} Certificate | {platform_name}').format(
            partner_short_name='edX',
            course_number='XSeries',
            platform_name=settings.PLATFORM_NAME,
        )
        return {
            'dir_rtl': 'rtl' if translation.get_language_bidi() else 'ltr',
            'LANGUAGE_CODE': self.request.LANGUAGE_CODE,
            'platform_name': settings.PLATFORM_NAME,
            'username': user_certificate.username,
            'uuid': user_certificate.uuid,
            'certificate_date_issued': certificate_date_issued,
            'document_title': document_title,
            'organization': {  # TODO will fix once retrieve orgs.
                'name': 'edX',
                'short_name': 'edx',
                'logo': '/static/images/logo-edx.png',
                'description': 'Testing description'
            },
            'program_course_count': 3  # TODO will fix once retrieve count.
        }
