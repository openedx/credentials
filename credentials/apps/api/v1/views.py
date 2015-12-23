"""
Credentials service API views (v1).
"""
import logging

from rest_framework import status
from rest_framework import viewsets, generics
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework import filters

from credentials.apps.api import exceptions
from credentials.apps.api.accreditor import Accreditor
from credentials.apps.api.serializers import (
    UserCredentialSerializer, ProgramCertificateSerializer,
    CourseCertificateSerializer
)
from credentials.apps.credentials.models import (
    UserCredential, ProgramCertificate, CourseCertificate
)


log = logging.getLogger(__name__)


class UserCredentialViewSet(viewsets.ModelViewSet):
    """ UserCredentials endpoints. """

    queryset = UserCredential.objects.all()
    lookup_field = 'id'
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('username', 'status')
    serializer_class = UserCredentialSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)

    def list(self, request, *args, **kwargs):
        if not self.request.query_params.get('username'):
            return Response({
                'error': 'Username is required for filtering user_credentials.'
            }, status=status.HTTP_400_BAD_REQUEST)

        return super(UserCredentialViewSet, self).list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        PATCH # /v1/user_credentials/{username}/
        Only to update the certificate status.
        {
            "id": 1,
            "username": "tester",
            "credential": {
                "program_id": 1001
            },
            "status": "revoked",
            "download_url": "",
            "uuid": "2a2f5562-b876-44c8-b16e-f62ea3a1a2e6",
            "attributes": []
        }
        """
        # if id exists in db then return the object otherwise return 404
        credential = generics.get_object_or_404(UserCredential, pk=request.data.get('id'))
        credential.status = request.data.get('status')
        if not credential.status:
            return Response({
                'error': 'Only status of credential is allowed to update'
            }, status=status.HTTP_400_BAD_REQUEST)

        credential.save()
        serializer = self.get_serializer(credential)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Create only one user credentials. For each record Accreditor class
        will get the issuer class object depending upon the credential type
        program-id and course id and issue the credential.

        # /v1/user_credentials/
        {
            "username": "user1",
            "program_id": 100,
            "attributes": [
                {
                    "namespace": "whitelist",
                    "name": "grades",
                    "value": "0.7"
                }
            ]
        }
        """
        try:
            credential = request.data
            credential_type = None
            cred_id = None

            if 'program_id' in credential:
                credential_type = ProgramCertificate.credential_type_slug
                cred_id = credential.get('program_id')
            elif 'course_id' in credential:
                credential_type = CourseCertificate.credential_type_slug
                cred_id = credential.get('course_id')

            if not credential_type:
                raise exceptions.UnsupportedCredentialTypeError("Credential type is missing.")

            if not isinstance(cred_id, int):
                raise exceptions.InvalidCredentialIdError(
                    "Credential Id [{cred_id}] is invalid.".format(cred_id=cred_id)
                )

            if 'username' not in credential:
                raise ValueError("Username is not available.")

            username = credential.pop('username')

            accreditor = Accreditor()
            user_credential = accreditor.issue_credential(credential_type, username, **credential)
            serializer = self.get_serializer(user_credential)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as ex:  # pylint: disable=broad-except
            return Response({'error': ex.message},
                            status=status.HTTP_400_BAD_REQUEST)


class CredentialsByProgramsViewSet(viewsets.ModelViewSet):
    """It will return the all credentials for programs."""
    lookup_field = 'program_id'
    queryset = ProgramCertificate.objects.all()
    serializer_class = ProgramCertificateSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)


class CredentialsByCoursesViewSet(viewsets.ModelViewSet):
    """It will return the all credentials for courses."""
    lookup_field = 'course_id'
    queryset = CourseCertificate.objects.all()
    serializer_class = CourseCertificateSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
