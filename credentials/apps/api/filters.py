"""Custom filters for credentials apis."""
import django_filters

from credentials.apps.credentials.models import UserCredential


class UserCredentialFilter(django_filters.FilterSet):
    """Search filter for usercredential model"""

    class Meta:
        model = UserCredential
        fields = ['username', 'status']
