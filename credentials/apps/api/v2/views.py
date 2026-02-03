import logging

from django.apps import apps
from django.db import transaction
from django.db.models import Q
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView, exception_handler

from credentials.apps.api.v2.decorators import log_incoming_request
from credentials.apps.api.v2.filters import UserCredentialFilter
from credentials.apps.api.v2.permissions import CanReplaceUsername, UserCredentialPermissions
from credentials.apps.api.v2.serializers import (
    CourseCertificateSerializer,
    UserCredentialCreationSerializer,
    UserCredentialSerializer,
    UserGradeSerializer,
)
from credentials.apps.credentials.models import CourseCertificate, UserCredential
from credentials.apps.records.models import UserGrade

log = logging.getLogger(__name__)


# NOTE: Although this is v2 and other APIs in this application are v1,
# the API naming and code layout convention here is not to be used for new
# endpoints, per:
# https://openedx.atlassian.net/wiki/spaces/AC/pages/18350757/edX+REST+API+Conventions


def credentials_throttle_handler(exc, context):
    """Exception handler for logging messages when an endpoint is throttled."""
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        view = context["view"]
        if isinstance(view, CredentialViewSet):
            view = "CredentialViewSet"
        elif isinstance(view, GradeViewSet):
            view = "GradeViewSet"

        log.warning(f"Credentials API endpoint {view} is being throttled.")

    return response


class CredentialRateThrottle(ScopedRateThrottle):
    """Rate limits requests to the credentials endpoints."""

    THROTTLE_RATES = {
        "credential_view": "15/minute",
        "grade_view": "90/minute",
        "staff_override": "1500/minute",
    }

    def allow_request(self, request, view):
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            view.throttle_scope = None

        return super().allow_request(request, view)


class CredentialViewSet(viewsets.ModelViewSet):
    filterset_class = UserCredentialFilter
    lookup_field = "uuid"
    permission_classes = (UserCredentialPermissions,)
    serializer_class = UserCredentialSerializer
    throttle_classes = (CredentialRateThrottle,)
    throttle_scope = "credential_view"

    def get_queryset(self):
        queryset = UserCredential.objects.all()

        # We have to filter on the explicit credential models
        # because we cannot set a GenericRelation field on the Site model.
        site = self.request.site
        queryset = queryset.filter(Q(program_credentials__site=site) | Q(course_credentials__site=site))

        return queryset

    def create(self, request, *args, **kwargs):
        """Create or update a credential.

        This endpoint does not work in the swagger docs because it is not configured to accept dicts.
        Use OPTIONS api/vX/credentials/ to understand the schema.
        ---
        serializer: UserCredentialCreationSerializer
        omit_parameters:
            - query
        """
        self.serializer_class = UserCredentialCreationSerializer
        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.revoke()

    def destroy(self, request, *args, **kwargs):
        """Revoke, but do NOT delete, a credential.
        ---
        omit_parameters:
            - query
        """
        super().destroy(request, *args, **kwargs)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """List all credentials."""
        return super().list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """Update a credential.
        ---
        omit_parameters:
            - query
        """
        return super().partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """Retrieve the details of a single credential.
        ---
        omit_parameters:
            - query
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):  # pylint: disable=useless-super-delegation
        """Update a credential.
        ---
        omit_parameters:
            - query
        """
        return super().update(request, *args, **kwargs)


# A write-only endpoint for now
class GradeViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = (UserCredentialPermissions,)
    serializer_class = UserGradeSerializer
    throttle_classes = (CredentialRateThrottle,)
    throttle_scope = "grade_view"
    queryset = UserGrade.objects.all()

    @log_incoming_request
    def create(self, request, *args, **kwargs):
        """Create a new grade."""
        return super().create(request, *args, **kwargs)

    @log_incoming_request
    def partial_update(self, request, *args, **kwargs):
        """Update a grade."""
        return super().partial_update(request, *args, **kwargs)

    @log_incoming_request
    def update(self, request, *args, **kwargs):
        """Update a grade."""
        return super().update(request, *args, **kwargs)


class UsernameReplacementView(APIView):
    """
    WARNING: This API is only meant to be used as part of a larger job that
    updates usernames across all services. DO NOT run this alone or users will
    not match across the system and things will be broken. This API should be
    called from the LMS endpoint which verifies uniqueness of the username
    first.

    API will receive a list of current usernames and their new username.
    """

    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanReplaceUsername)

    def post(self, request):
        """
        **POST Parameters**

        A POST request must include the following parameter.

        * username_mappings: Required. A list of objects that map the current username (key)
          to the new username (value)
            {
                "username_mappings": [
                    {"current_username_1": "new_username_1"},
                    {"current_username_2": "new_username_2"}
                ]
            }

        **POST Response Values**

        As long as data validation passes, the request will return a 200 with a new mapping
        of old usernames (key) to new username (value)

        {
            "successful_replacements": [
                {"old_username_1": "new_username_1"}
            ],
            "failed_replacements": [
                {"old_username_2": "new_username_2"}
            ]
        }
        """
        # (model_name, column_name)
        MODELS_WITH_USERNAME = (
            ("core.user", "username"),
            ("credentials.usercredential", "username"),
            ("records.usergrade", "username"),
        )
        username_mappings = request.data.get("username_mappings")

        replacement_locations = self._load_models(MODELS_WITH_USERNAME)

        if not self._has_valid_schema(username_mappings):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        successful_replacements, failed_replacements = [], []

        for username_pair in username_mappings:
            current_username = list(username_pair.keys())[0]
            new_username = list(username_pair.values())[0]
            successfully_replaced = self._replace_username_for_all_models(
                current_username, new_username, replacement_locations
            )
            if successfully_replaced:
                successful_replacements.append({current_username: new_username})
            else:
                failed_replacements.append({current_username: new_username})
        return Response(
            status=status.HTTP_200_OK,
            data={"successful_replacements": successful_replacements, "failed_replacements": failed_replacements},
        )

    def _load_models(self, models_with_fields):
        """Takes tuples that contain a model path and returns the list with a loaded version of the model"""
        try:
            replacement_locations = [(apps.get_model(model), column) for (model, column) in models_with_fields]
        except LookupError:
            log.exception("Unable to load models for username replacement")
            raise
        return replacement_locations

    def _has_valid_schema(self, post_data):
        """Verifies the data is a list of objects with a single key:value pair"""
        if not isinstance(post_data, list):
            return False
        for obj in post_data:
            if not (isinstance(obj, dict) and len(obj) == 1):
                return False
        return True

    def _replace_username_for_all_models(self, current_username, new_username, replacement_locations):
        """
        Replaces current_username with new_username for all (model, column) pairs in replacement locations.
        Returns if it was successful or not. Usernames that don't exist in this service will be treated as
        a success because no work needs to be done changing their username.
        """
        try:
            with transaction.atomic():
                num_rows_changed = 0
                for model, column in replacement_locations:
                    num_rows_changed += model.objects.filter(**{column: current_username}).update(
                        **{column: new_username}
                    )
        except Exception as exc:
            log.exception(
                "Unable to change username from %s to %s. Failed on table %s because %s",
                current_username,
                new_username,
                model.__class__.__name__,
                exc,
            )
            return False
        if num_rows_changed == 0:
            log.info(
                "Unable to change username from %s to %s because %s doesn't exist.",
                current_username,
                new_username,
                current_username,
            )
        else:
            log.info(
                "Successfully changed username from %s to %s.",
                current_username,
                new_username,
            )
        return True


class CourseCertificateViewSet(
    mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = CourseCertificate.objects.all()
    serializer_class = CourseCertificateSerializer
    permission_classes = (permissions.IsAdminUser,)
    lookup_field = "course_id"
