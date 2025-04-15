"""
Verifiable Credentials API v1 views.
"""

import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credentials.apps.credentials.models import UserCredential
from credentials.apps.verifiable_credentials.issuance import IssuanceException
from credentials.apps.verifiable_credentials.issuance.main import CredentialIssuer
from credentials.apps.verifiable_credentials.issuance.serializers import StorageSerializer
from credentials.apps.verifiable_credentials.issuance.status_list import issue_status_list
from credentials.apps.verifiable_credentials.issuance.utils import get_issuer_ids
from credentials.apps.verifiable_credentials.permissions import VerifiablePresentation
from credentials.apps.verifiable_credentials.storages.utils import get_available_storages, get_storage
from credentials.apps.verifiable_credentials.utils import (
    generate_base64_qr_code,
    get_user_credentials_data,
    is_valid_uuid,
)


logger = logging.getLogger(__name__)

User = get_user_model()


class CredentialsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A view set to list all credentials issued to the authenticated user.
    Supports filtering by credential type.

    Credential Types:
        - programcertificate: Credentials associated with a program.
        - coursecertificate: Credentials associated with a course.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )

    permission_classes = (IsAuthenticated,)

    CREDENTIAL_TYPES_MAP = {
        "programcertificate": "program_credentials",
        "coursecertificate": "course_credentials",
    }

    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of issued credentials for the authenticated user.

        GET: /verifiable_credentials/api/v1/credentials?types=coursecertificate,programcertificate

        Query Parameters:
            types (str, optional): A comma-separated list of credential types to filter the results.
                                   Valid types are "programcertificate" and "coursecertificate".
                                   If not provided, all credential types will be included.

        Arguments:
            request: The HTTP request object containing the query parameters.

        Returns:
            response(dict): A dictionary where each key corresponds to a credential type, and the value
                            is a list of issued credentials for that type.

        Example Response:
            {
                "program_credentials": [
                    {
                        "uuid": "4a665745d1ba4dfd8f54b58e822b6585",
                        "status": "awarded",
                        "username": "staff",
                        "credential_id": 1,
                        "credential_uuid": "525756b010aa4c788881141acca72538",  # Program UUID
                        "credential_title": "Title of a program",
                        "credential_org": "",
                        "modified_date": "2024-12-18"
                    }
                ],
                "course_credentials": [
                    {
                        "uuid": "5135e99ef1d14bca9135972270ef887b",
                        "status": "awarded",
                        "username": "staff",
                        "credential_id": 1,
                        "credential_uuid": "course-v1:rg+program_course+2024",  # Course ID
                        "credential_title": "Course cert configuration",
                        "credential_org": "rg",
                        "modified_date": "2024-12-18"
                    }
                ]
            }
        """
        types = self.request.query_params.get("types")
        response = {}

        if types:
            types = types.split(",")
        else:
            types = self.CREDENTIAL_TYPES_MAP.keys()

        for credential_type in types:
            if credential_type in self.CREDENTIAL_TYPES_MAP:
                response[self.CREDENTIAL_TYPES_MAP[credential_type]] = get_user_credentials_data(
                    request.user.username, credential_type
                )

        return Response(response)


class InitIssuanceView(APIView):
    """
    Generates a deeplink, qrcode for VC issuance process initiation.

    POST: /verifiable_credentials/api/v1/credentials/init

    POST Parameters:
        * credential_id: Required. An unique UserCredential identifier.
        * storage_id: Required. Requested storage (wallet) identifier.
    Returns:
        response(dict): parametrized deep link, qrcode and mobile app links
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        credential_uuid = request.data.get("credential_uuid")
        storage_id = request.data.get("storage_id")

        if not credential_uuid:
            msg = _("Mandatory data is missing")
            logger.exception(msg)
            raise ValidationError({"credential_uuid": msg})

        if not is_valid_uuid(credential_uuid):
            msg = _("Credential identifier must be valid UUID: ['credential_uuid']")
            logger.exception(msg)
            raise ValidationError({"credential_uuid": msg})

        if not storage_id:
            msg = _("Mandatory data is missing")
            logger.exception(msg)
            raise ValidationError({"storage_id": msg})

        # validate given user credential exists:
        user_credential = UserCredential.objects.filter(uuid=credential_uuid).first()
        if not user_credential:
            msg = _("No such user credential [%(credential_uuid)s]") % {"credential_uuid": credential_uuid}
            logger.exception(msg)
            raise NotFound({"credential_uuid": msg})

        # validate given storage is active:
        storage = get_storage(storage_id)
        if not storage:
            available_storages_ids = [storage.ID for storage in get_available_storages()]
            msg = _(
                "Provided storage backend ({storage_id}) isn't active. \
                Storages: {active_storages}"
            ).format(storage_id=storage_id, active_storages=available_storages_ids)
            logger.exception(msg)
            raise NotFound({"storage_id": msg})

        # initiate new issuance line now:
        issuance_line = CredentialIssuer.init(
            user_credential=user_credential,
            storage_id=storage_id,
        )

        deeplink = issuance_line.storage.get_deeplink_url(issuance_line)

        init_data = {
            "deeplink": deeplink,
            "qrcode": generate_base64_qr_code(deeplink),
        }

        # auto-redirect to web storage:
        if issuance_line.storage.is_web():
            init_data.update(
                {
                    "redirect": True,
                }
            )

        if issuance_line.storage.is_mobile():
            init_data.update(
                {
                    "app_link_android": issuance_line.storage.APP_LINK_ANDROID,
                    "app_link_ios": issuance_line.storage.APP_LINK_IOS,
                }
            )

        return Response(init_data)


class IssueCredentialView(APIView):
    """
    This API endpoint allows requests for VC issuing.

    POST: /verifiable_credentials/api/v1/credential/issue

    Request and response should conform VC API specs:
    https://w3c-ccg.github.io/vc-api/#issue-credential
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated | VerifiablePresentation,)

    def post(self, request, *args, **kwargs):
        try:
            credential_issuer = CredentialIssuer(data=request.data, issuance_uuid=kwargs.get("issuance_line_uuid"))
            verifiable_credential = credential_issuer.issue()
            return Response(verifiable_credential, status=status.HTTP_201_CREATED)
        except IssuanceException as exc:
            raise ValidationError({"issuance_issue": exc.detail})


class AvailableStoragesView(ListAPIView):
    """
    List data for all available storages.

    GET: /verifiable_credentials/api/v1/storages/
    Arguments:
        request: A request to control data returned in endpoint response
    Returns:
        response(dict): List of available storages
    """

    serializer_class = StorageSerializer
    pagination_class = None
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return get_available_storages()


class StatusList2021View(APIView):
    """
    Verifiable credentials status verification.

    GET: /verifiable_credentials/api/v1/status-list/2021/v1/<issuer-ID>/
    """

    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        issuer_id = kwargs["issuer_id"]

        if issuer_id not in get_issuer_ids():
            msg = _("Can't find an Issuer with such ID [{issuer_id}]").format(issuer_id=issuer_id)
            logger.exception(msg)
            raise NotFound({"reason": msg})

        try:
            status_list = issue_status_list(issuer_id=issuer_id)
            return Response(status_list)
        except IssuanceException as exc:
            raise ValidationError({"reason": exc.detail})
