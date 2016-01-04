"""
Credentials service API views (v1).
"""
import logging

from rest_framework import filters, mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from credentials.apps.api.filters import ProgramFilter, CourseFilter

from credentials.apps.api.serializers import UserCredentialCreationSerializer, UserCredentialSerializer
from credentials.apps.credentials.models import UserCredential


log = logging.getLogger(__name__)


class UserCredentialViewSet(viewsets.ModelViewSet):
    """ UserCredentials endpoints. """

    queryset = UserCredential.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('username', 'status')
    serializer_class = UserCredentialSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)

    def list(self, request, *args, **kwargs):
        if not self.request.query_params.get('username'):
            raise ValidationError(
                {'error': 'A username query string parameter is required for filtering user credentials.'})

        return super(UserCredentialViewSet, self).list(request, *args, **kwargs)  # pylint: disable=maybe-no-member

    def create(self, request, *args, **kwargs):
        self.serializer_class = UserCredentialCreationSerializer
        return super(UserCredentialViewSet, self).create(request, *args, **kwargs)


class ProgramsCredentialsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """It will return the all credentials for programs."""
    queryset = UserCredential.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ProgramFilter
    serializer_class = UserCredentialSerializer

    def list(self, request, *args, **kwargs):
        if not self.request.query_params.get('program_id'):
            raise ValidationError(
                {'error': 'A program_id query string parameter is required for filtering program credentials.'})

        # pylint: disable=maybe-no-member
        return super(ProgramsCredentialsViewSet, self).list(request, *args, **kwargs)


class CourseCredentialsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """It will return the all credentials for courses."""
    queryset = UserCredential.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CourseFilter
    serializer_class = UserCredentialSerializer

    def list(self, request, *args, **kwargs):
        if not self.request.query_params.get('course_id'):
            raise ValidationError(
                {'error': 'A course_id query string parameter is required for filtering course credentials.'})

        # pylint: disable=maybe-no-member
        return super(CourseCredentialsViewSet, self).list(request, *args, **kwargs)
