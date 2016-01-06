"""
Reusable queryset filters for the REST API.
"""
import django_filters
from credentials.apps.credentials.models import UserCredential


class ProgramFilter(django_filters.FilterSet):
    """ Allows for filtering program credentials by their program_id and status
    using a query string argument.
    """
    program_id = django_filters.NumberFilter(name="program_credentials__program_id")

    class Meta:
        model = UserCredential
        fields = ['program_id', 'status']


class CourseFilter(django_filters.FilterSet):
    """ Allows for filtering course credentials by their course_id, status and
    certificate_type using a query string argument.
    """
    course_id = django_filters.CharFilter(name="course_credentials__course_id")
    certificate_type = django_filters.CharFilter(name="course_credentials__certificate_type")

    class Meta:
        model = UserCredential
        fields = ['course_id', 'status', 'certificate_type']
