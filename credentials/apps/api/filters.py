import django_filters
from credentials.apps.credentials.models import UserCredential


class ProgramFilter(django_filters.FilterSet):
    program_id = django_filters.NumberFilter(name="programs_credentials__program_id")
    credential_id = django_filters.NumberFilter(name="programs_credentials__id")

    class Meta:
        model = UserCredential
        fields = ['program_id', 'status', 'credential_id']


class CourseFilter(django_filters.FilterSet):

    def filter_course_id(queryset, value):
        # drf replace + signs with spaces.
        return queryset.filter(
            courses_credentials__course_id=value.replace(' ', '+')
        )

    course_id = django_filters.MethodFilter(action=filter_course_id)
    credential_id = django_filters.CharFilter(name="courses_credentials__id")
    certificate_type = django_filters.CharFilter(name="courses_credentials__certificate_type")

    class Meta:
        model = UserCredential
        fields = ['course_id', 'status', 'credential_id']
