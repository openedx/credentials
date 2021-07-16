from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from credentials.apps.records.rest_api.v1.serializers import ProgramSerializer
from credentials.apps.records.utils import get_user_program_data


class ProgramRecords(APIView):

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get data for all the user's enrolled programs
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
