import logging

from django.http import Http404
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination

from credentials.apps.api.filters import CourseFilter
from credentials.apps.api.permissions import UserCredentialViewSetPermissions
from credentials.apps.api.serializers import UserCredentialCreationSerializer, UserCredentialSerializer
from credentials.apps.api.v1.filters import UserCredentialFilter
from credentials.apps.credentials.models import UserCredential

log = logging.getLogger(__name__)


class UserCredentialViewSet(viewsets.ModelViewSet):
    """ UserCredentials endpoints. """

    queryset = UserCredential.objects.all()
    filter_fields = ('username', 'status')
    serializer_class = UserCredentialSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (UserCredentialViewSetPermissions,)

    def list(self, request, *args, **kwargs):
        if not request.query_params.get('username'):
            raise ValidationError(
                {'error': 'A username query string parameter is required for filtering user credentials.'})

        # provide an additional permission check related to the username
        # query string parameter.  See also `UserCredentialViewSetPermissions`
        if not request.user.has_perm('credentials.view_usercredential') and (
                request.user.username.lower() != request.query_params['username'].lower()
        ):
            raise Http404

        return super(UserCredentialViewSet, self).list(request, *args, **kwargs)  # pylint: disable=maybe-no-member

    def create(self, request, *args, **kwargs):
        self.serializer_class = UserCredentialCreationSerializer
        return super(UserCredentialViewSet, self).create(request, *args, **kwargs)


class ProgramsCredentialsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """It will return the all credentials for programs."""
    queryset = UserCredential.objects.all()
    filter_class = UserCredentialFilter
    pagination_class = LimitOffsetPagination
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
    filter_class = CourseFilter
    pagination_class = LimitOffsetPagination
    serializer_class = UserCredentialSerializer

    def list(self, request, *args, **kwargs):
        if not self.request.query_params.get('course_id'):
            raise ValidationError(
                {'error': 'A course_id query string parameter is required for filtering course credentials.'})

        # pylint: disable=maybe-no-member
        return super(CourseCredentialsViewSet, self).list(request, *args, **kwargs)
