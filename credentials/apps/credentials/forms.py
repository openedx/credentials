"""
Django forms for the credentials
"""
from django import forms

from credentials.apps.credentials.models import Signatory


class SignatoryModelForm(forms.ModelForm):
    """Signatory form with updated model fields."""
    title = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Signatory
        fields = '__all__'
