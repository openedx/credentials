import django_filters
from credentials.apps.credentials.models import UserCredential


class ProgramFilter(django_filters.FilterSet):
    program_id = django_filters.NumberFilter(name="programs_credentials__program_id")
    credential_id = django_filters.CharFilter(name="programs_credentials__id")

    class Meta:
        model = UserCredential
        fields = ['program_id', 'status', 'credential_id']
