import django_filters
from django.utils.translation import ugettext_lazy as _

from credentials.apps.credentials.models import UserCredential


class UserCredentialFilter(django_filters.FilterSet):
    program_uuid = django_filters.UUIDFilter(
        name='program_credentials__program_uuid',
        label=_('UUID of the program for which the credential was awarded')
    )
    status = django_filters.ChoiceFilter(
        choices=UserCredential._meta.get_field('status').choices,
        label=_('Status of the credential')
    )
    username = django_filters.CharFilter(label=_('Username of the recipient of the credential'))

    class Meta:
        model = UserCredential
        fields = ['program_uuid', 'status', 'username', ]
