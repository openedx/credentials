from django import forms
from django.utils.translation import ugettext as _

from credentials.apps.core.models import SiteConfiguration


class SiteConfigurationAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['enable_facebook_sharing'] and not cleaned_data['facebook_app_id']:
            message = _('A Facebook app ID is required to enable Facebook sharing.')
            self.add_error('facebook_app_id', forms.ValidationError(message, code='required_for_sharing'))

        return cleaned_data

    class Meta:
        model = SiteConfiguration
        fields = '__all__'
