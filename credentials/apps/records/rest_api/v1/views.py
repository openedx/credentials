import logging

from django.contrib.auth import get_user_model
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from credentials.apps.records.api import get_program_details
from credentials.apps.records.models import ProgramCertRecord
from credentials.apps.records.rest_api.v1.permissions import CanAccessProgramRecord, IsPublic
from credentials.apps.records.rest_api.v1.serializers import ProgramRecordSerializer, ProgramSerializer
from credentials.apps.records.utils import get_user_program_data


User = get_user_model()
log = logging.getLogger(__name__)


class ProgramRecordsViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (
        IsPublic,
        CanAccessProgramRecord,
    )

    def list(self, request, *args, **kwargs):
        """
        List data for all the user's enrolled programs
        GET: /records/api/v1/program_records/

        Arguments:
            request: A request to control data returned in endpoint response

        Returns:
            response(dict): Information about the user's enrolled programs
        """
        # Check for a username query parameter.
        # If there is one in the request, we will pass it into the `get_user_program_data` function.
        # If there is no username query parameter, we instead pass the username from the user in the request.
        query_param_username = request.query_params.get("username", "")
        username = request.user.username

        if query_param_username:
            try:
                User.objects.get(username=query_param_username)
            except User.DoesNotExist:
                log.error(f'A user matching the username "{query_param_username}" does not exist')
                return Response(status=status.HTTP_404_NOT_FOUND)
            else:
                # Overwrite username variable once we know a User with that username exists
                username = query_param_username

        programs = get_user_program_data(
            username, request.site, include_empty_programs=False, include_retired_programs=True
        )

        serializer = ProgramSerializer(programs, many=True)
        return Response({"enrolled_programs": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieving data for a specific program by its ID
        GET: /records/api/v1/program_records/:program_uuid/

        Arguments:
            kwargs: Access to uuid as 'pk' in keyword arguments

        Returns:
            response(dict): Details about a user's progress in a given program
        """
        # Query parameters come through as a string and we need to convert it to a boolean
        query_param_is_public = request.query_params.get("is_public", "")
        is_public = query_param_is_public.lower() == "true"

        # Check for a username query parameter.
        # If there is one in the request, we will fetch the User associated with that username.
        # This Django User object is passed into the `get_program_details` function.
        # If there is no username query parameter, we instead pass the user from the request.
        query_param_username = request.query_params.get("username", "")
        user = request.user

        try:
            if query_param_username:
                try:
                    searched_user = User.objects.get(username=query_param_username)
                except User.DoesNotExist:
                    log.error(f'A user matching the username "{query_param_username}" does not exist')
                    return Response(status=status.HTTP_404_NOT_FOUND)
                else:
                    # Overwrite user variable to be the fetched User
                    user = searched_user

            program = get_program_details(
                request_user=user,
                request_site=request.site,
                uuid=kwargs["pk"],
                is_public=is_public,
            )

        except ProgramCertRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ProgramRecordSerializer(program)

        return Response(serializer.data)
