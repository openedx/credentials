import logging

from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import exception_handler

from credentials.apps.api.v2.filters import UserCredentialFilter
from credentials.apps.api.v2.permissions import UserCredentialPermissions
from credentials.apps.api.v2.serializers import (UserCredentialCreationSerializer, UserCredentialSerializer,
                                                 UserGradeSerializer)
from credentials.apps.credentials.models import UserCredential
from credentials.apps.records.models import UserGrade

log = logging.getLogger(__name__)


def credentials_throttle_handler(exc, context):
    """ Exception handler for logging messages when an endpoint is throttled. """
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        view = context['view']
        if isinstance(view, CredentialViewSet):
            view = 'CredentialViewSet'
        elif isinstance(view, GradeViewSet):
            view = 'GradeViewSet'

        log.warning('Credentials API endpoint {} is being throttled.'.format(view))

    return response


class CredentialRateThrottle(ScopedRateThrottle):
    """ Rate limits requests to the credentials endpoints. """

    THROTTLE_RATES = {
        'credential_view': '15/minute',
        'grade_view': '90/minute',
        'staff_override': '200/minute',
    }

    def allow_request(self, request, view):
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            setattr(view, 'throttle_scope', 'staff_override')

        return super(CredentialRateThrottle, self).allow_request(request, view)


class CredentialViewSet(viewsets.ModelViewSet):
    filter_class = UserCredentialFilter
    lookup_field = 'uuid'
    permission_classes = (UserCredentialPermissions,)
    serializer_class = UserCredentialSerializer
    throttle_classes = (CredentialRateThrottle,)
    throttle_scope = 'credential_view'

    def get_queryset(self):
        queryset = UserCredential.objects.all()

        # We have to filter on the explicit credential models
        # because we cannot set a GenericRelation field on the Site model.
        site = self.request.site
        queryset = queryset.filter(Q(program_credentials__site=site) | Q(course_credentials__site=site))

        return queryset

    def create(self, request, *args, **kwargs):
        """ Create or update a credential.

        This endpoint does not work in the swagger docs because it is not configured to accept dicts.
        Use OPTIONS api/vX/credentials/ to understand the schema.
        ---
        serializer: UserCredentialCreationSerializer
        omit_parameters:
            - query
        """
        self.serializer_class = UserCredentialCreationSerializer
        return super(CredentialViewSet, self).create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.revoke()

    def destroy(self, request, *args, **kwargs):
        """ Revoke, but do NOT delete, a credential.
        ---
        omit_parameters:
            - query
        """
        super(CredentialViewSet, self).destroy(request, *args, **kwargs)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ List all credentials. """
        return super(CredentialViewSet, self).list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ Update a credential.
        ---
        omit_parameters:
            - query
        """
        return super(CredentialViewSet, self).partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ Retrieve the details of a single credential.
        ---
        omit_parameters:
            - query
        """
        return super(CredentialViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ Update a credential.
        ---
        omit_parameters:
            - query
        """
        return super(CredentialViewSet, self).update(request, *args, **kwargs)


# A write-only endpoint for now
class GradeViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    permission_classes = (UserCredentialPermissions,)
    serializer_class = UserGradeSerializer
    throttle_classes = (CredentialRateThrottle,)
    throttle_scope = 'grade_view'
    queryset = UserGrade.objects.all()

    def create(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ Create a new grade. """
        return super(GradeViewSet, self).create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ Update a grade. """
        return super(GradeViewSet, self).partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """ Update a grade. """
        return super(GradeViewSet, self).update(request, *args, **kwargs)
