import logging

from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from credentials.apps.credentials.rest_api.v1.permissions import CanGetLearnerStatus
from credentials.apps.records.api import get_learner_course_run_status


log = logging.getLogger(__name__)


class LearnerCertificateStatusView(APIView):
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )

    permission_classes = (
        permissions.IsAuthenticated,
        CanGetLearnerStatus,
    )

    lms_user_id_schema = openapi.Schema(type=openapi.TYPE_INTEGER, description="lms_user_id")

    username_schema = openapi.Schema(type=openapi.TYPE_STRING, description="username")

    per_course_grade_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "letter_grade": openapi.Schema(type=openapi.TYPE_STRING),
            "percent_grade": openapi.Schema(type=openapi.FORMAT_DECIMAL),
            "verified": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        },
    )
    course_run_object_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "uuid": openapi.Schema(type=openapi.TYPE_STRING),
            "key": openapi.Schema(type=openapi.TYPE_STRING),
            "status": openapi.Schema(type=openapi.TYPE_STRING),
            "type": openapi.Schema(type=openapi.TYPE_STRING),
            "certificate_available_date": openapi.Schema(type=openapi.FORMAT_DATE),
            "grade": per_course_grade_schema,
        },
    )
    per_course_status_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "course_uuid": openapi.TYPE_STRING,
            "course_run": course_run_object_schema,
        },
    )

    learner_cert_status_request_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "lms_user_id": lms_user_id_schema,
            "username": username_schema,
            "courses": openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="array of strings"
            ),
            "course_runs": openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="array of strings"
            ),
        },
    )

    learner_cert_status_return_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "lms_user_id": lms_user_id_schema,
            "username": username_schema,
            "status": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=course_run_object_schema,
            ),
        },
    )

    learner_cert_status_responses = {
        status.HTTP_200_OK: learner_cert_status_return_schema,
    }

    @swagger_auto_schema(
        request_body=learner_cert_status_request_schema,
        responses=learner_cert_status_responses,
    )
    def post(self, request):
        """
        A POST request must include one of "lms_user_id" or "username",
        and a list of course uuids, course_runs, or a mix of both.
        (or a program uuid, in a future version)
        """
        lms_user_id = request.data.get("lms_user_id")
        username = request.data.get("username")

        # only one of username or lms_user_id can be used
        if (username and lms_user_id) or not (username or lms_user_id):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )
        User = get_user_model()

        try:
            if username:
                user = User.objects.get(username=username)
                lms_user_id = user.lms_user_id
            else:
                user = User.objects.get(lms_user_id=lms_user_id)
                username = user.username
        except User.DoesNotExist:
            # we don't have the user in the system
            log.warning(
                f"No user with username {username} or lms_id {lms_user_id} available for learner certificate status."
            )
            return Response(status=status.HTTP_404_NOT_FOUND)

        course_ids = request.data.get("courses")

        course_runs = request.data.get("course_runs")

        courses = get_learner_course_run_status(username, course_ids, course_runs)

        return Response(
            status=status.HTTP_200_OK,
            data={"lms_user_id": lms_user_id, "username": username, "status": courses},
        )
