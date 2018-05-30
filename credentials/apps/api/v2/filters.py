import django_filters
from django.db.models import Q

from credentials.apps.catalog.models import Program
from credentials.apps.credentials.models import UserCredential


class ProgramRelatedFilter(django_filters.Filter):
    def filter(self, qs, value):
        program = Program.objects.filter(uuid=value).first()
        course_runs = [run.key for run in program.course_runs.all()] if program else []
        return qs.filter(Q(program_credentials__program_uuid=value) |
                         Q(course_credentials__course_id__in=course_runs))


class CredentialTypeFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value == 'program':
            return qs.filter(program_credentials__isnull=False)
        elif value == 'course-run':
            return qs.filter(course_credentials__isnull=False)
        return qs


class UserCredentialFilter(django_filters.FilterSet):
    program_uuid = ProgramRelatedFilter(
        label='UUID of the program for which the credential was awarded'
    )
    type = CredentialTypeFilter(
        label='Type of the credential (program or course-run)'
    )
    status = django_filters.ChoiceFilter(
        choices=UserCredential._meta.get_field('status').choices,
        label='Status of the credential'
    )
    username = django_filters.CharFilter(label='Username of the recipient of the credential')

    class Meta:
        model = UserCredential
        fields = ['program_uuid', 'type', 'status', 'username', ]
