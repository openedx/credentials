import django_filters

from credentials.apps.credentials.models import UserCredential


class UserCredentialFilter(django_filters.FilterSet):
    """ Allows for filtering program credentials by their program_uuid and status
    using a query string argument.
    """
    program_uuid = django_filters.UUIDFilter(name="program_credentials__program_uuid")

    class Meta:
        model = UserCredential
        fields = ['program_uuid', 'status']
