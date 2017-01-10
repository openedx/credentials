import logging

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
    queryset = UserCredential.objects.all()
    serializer_class = UserCredentialSerializer

    def create(self, request, *args, **kwargs):
        self.serializer_class = UserCredentialCreationSerializer
        return super(CredentialViewSet, self).create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.revoke()

    def destroy(self, request, *args, **kwargs):
        """ Revoke, but do NOT delete, a credential. """
        super(CredentialViewSet, self).destroy(request, *args, **kwargs)  # pylint: disable=no-member
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
