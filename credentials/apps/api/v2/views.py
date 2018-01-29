import logging

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response

from credentials.apps.api.v2.filters import UserCredentialFilter
from credentials.apps.api.v2.permissions import UserCredentialPermissions
from credentials.apps.api.v2.serializers import UserCredentialCreationSerializer, UserCredentialSerializer
from credentials.apps.credentials.models import UserCredential

log = logging.getLogger(__name__)


class CredentialViewSet(viewsets.ModelViewSet):
    filter_class = UserCredentialFilter
    lookup_field = 'uuid'
    permission_classes = (UserCredentialPermissions,)
    serializer_class = UserCredentialSerializer

    def get_queryset(self):
        queryset = UserCredential.objects.all()

        # We have to filter on the explicit credential models
        # because we cannot set a GenericRelation field on the Site model.
        site = self.request.site
        queryset = queryset.filter(Q(program_credentials__site=site) | Q(course_credentials__site=site))

        return queryset

    def create(self, request, *args, **kwargs):
        """ Create a new credential.

        This endpoint does not work in the swagger docs because it is not configured to accept dicts.
        Use OPTIONS api/v<version>/credentials/ to understand the schema.
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
