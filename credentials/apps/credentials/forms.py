"""
Django forms for the credentials
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from credentials.apps.credentials.models import ProgramCertificate, Signatory


class SignatoryModelForm(forms.ModelForm):
    """Signatory form with updated model fields."""
    title = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Signatory
        fields = '__all__'


class ProgramCertificateAdminForm(forms.ModelForm):
    class Meta:
        model = ProgramCertificate
        fields = '__all__'

    def clean(self):
        cleaned_data = super(ProgramCertificateAdminForm, self).clean()

        site = cleaned_data['site']
        program_uuid = cleaned_data['program_uuid']
        program = site.siteconfiguration.get_program(program_uuid, ignore_cache=True)

        # Ensure the program's authoring organizations all have certificate logos
        for organization in program.get('authoring_organizations', []):
            if not organization.get('certificate_logo_image_url'):
                self.add_error(
                    'program_uuid',
                    _('All authoring organizations of the program MUST have a certificate image defined!')
                )
                break

        return cleaned_data
