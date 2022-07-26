from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from credentials.apps.records.api import get_program_details
from credentials.apps.records.models import ProgramCertRecord
from credentials.apps.records.rest_api.v1.serializers import ProgramRecordSerializer, ProgramSerializer
from credentials.apps.records.utils import get_user_program_data


class ProgramRecordsViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        """
        List data for all the user's enrolled programs
        GET: /records/api/v1/program_records/

        Arguments:
            request: A request to control data returned in endpoint response

        Returns:
            response(dict): Information about the user's enrolled programs
        """
        programs = get_user_program_data(
            request.user.username, request.site, include_empty_programs=False, include_retired_programs=True
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
        # query parameters come through as a string and we need to convert it to a boolean
        query_param_is_public = request.query_params.get("is_public", "")
        is_public = query_param_is_public.lower() == "true"

        try:
            program = get_program_details(
                request_user=request.user,
                request_site=request.site,
                uuid=kwargs["pk"],
                is_public=is_public,
            )
        except ProgramCertRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ProgramRecordSerializer(program)

        return Response(serializer.data)
