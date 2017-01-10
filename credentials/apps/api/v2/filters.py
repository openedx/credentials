import django_filters

from credentials.apps.credentials.models import UserCredential


class UserCredentialFilter(django_filters.FilterSet):
    program_uuid = django_filters.UUIDFilter(name='program_credentials__program_uuid')

    class Meta:
        model = UserCredential
        fields = ['program_uuid', 'status', 'username', ]
