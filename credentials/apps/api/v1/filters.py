import django_filters

from credentials.apps.credentials.models import UserCredential


class UserCredentialFilter(django_filters.FilterSet):
    """ Allows for filtering program credentials by their program_id and status
    using a query string argument.
    """
    program_id = django_filters.NumberFilter(name="program_credentials__program_id")

    class Meta:
        model = UserCredential
        fields = ['program_id', 'status']
