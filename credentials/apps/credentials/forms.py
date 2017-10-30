"""
Django forms for the credentials
"""
from operator import itemgetter

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from credentials.apps.credentials.models import ProgramCertificate, Signatory


class SignatoryModelForm(forms.ModelForm):
    """Signatory form with updated model fields."""
    title = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Signatory
        fields = '__all__'


class ProgramCertificateAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProgramCertificateAdminForm, self).__init__(*args, **kwargs)
        languages = settings.CERTIFICATE_LANGUAGES.items()
        lang_choices = sorted(languages, key=itemgetter(1))
        self.fields['language'] = forms.ChoiceField(
            choices=lang_choices, required=False
        )

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
