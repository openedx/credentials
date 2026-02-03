import logging
from typing import Dict, List, Optional

from django.core.exceptions import BadRequest
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from credentials.apps.credentials.rest_api.v1.permissions import CanGetLearnerStatus
from credentials.apps.records.api import single_learner_cert_status

log = logging.getLogger(__name__)


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


bulk_learner_cert_status_request_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=openapi.Items(type=learner_cert_status_request_schema),
    description="array of learner_cert_status_request objects",
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

bulk_learner_cert_status_return_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=openapi.Items(type=learner_cert_status_return_schema),
    description="array of learner_cert_status_return objects",
)


class LearnerCertificateStatusView(APIView):
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )

    permission_classes = (
        permissions.IsAuthenticated,
        CanGetLearnerStatus,
    )
    learner_cert_status_responses = {
        status.HTTP_200_OK: learner_cert_status_return_schema,
    }

    @swagger_auto_schema(
        request_body=learner_cert_status_request_schema,
        responses=learner_cert_status_responses,
    )
    def post(self, request):
        """Query for earned certificates for a user.

        Query for an individuals user's earned certificates for a list of courses or course runs.

        * You must include _exactly one_ of `lms_user_id` or `username`.
        * You must include at least one of `courses` and `course_runs`, and you may include a mix of both.
            * The `courses` list should contain a list of course UUIDs.
            * The `course_runs` list should contain a list of course run keys.

        If the `username` or `lms_user_id` has not earned any certificates, this endpoint
        will return successfully, and the `status` object will be empty.
        """
        lms_user_id = request.data.get("lms_user_id")  # type: Optional[int]
        username = request.data.get("username")  # type: Optional[str]
        course_ids = request.data.get("courses")  # type: Optional[List[str]]
        course_runs = request.data.get("course_runs")  # type: Optional[List[str]]

        try:
            return Response(
                status=status.HTTP_200_OK,
                data=single_learner_cert_status(lms_user_id, username, course_ids, course_runs),
            )
        except BadRequest:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )


class BulkLearnerCertificateStatusView(APIView):
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )

    permission_classes = (
        permissions.IsAuthenticated,
        CanGetLearnerStatus,
    )
    bulk_learner_cert_status_responses = {
        status.HTTP_200_OK: bulk_learner_cert_status_return_schema,
    }

    @swagger_auto_schema(
        request_body=bulk_learner_cert_status_request_schema,
        responses=bulk_learner_cert_status_responses,
    )
    def post(self, request):
        """Query for earned certificates for a list of users.

        Query for list of user's earned certificates for a list of courses or course runs.

        In each object in the list describing a user/course combination:

        * You must include _exactly one_ of `lms_user_id` or `username`.
        * You must include at least one of `courses` and `course_runs`, and you may include a mix of both.
            * The `courses` list should contain a list of course UUIDs.
            * The `course_runs` list should contain a list of course run keys.

        If the `username` or `lms_user_id` has not earned any certificates, the `status` object will be
        empty for that user.

        If any individual object in the list describing a user/course is invalid
        and cannot be resolved to a single learner's identity (e.g. does not
        include exactly one lms_user_id or username), that object will be
        skipped and there will be no corresponding entry in the return list.
        """
        request_list = request.data  # type: Optional[List[Dict]]
        response_list = []

        for req in request_list:
            lms_user_id = req.get("lms_user_id")  # type: Optional[int]
            username = req.get("username")  # type: Optional[str]
            course_ids = req.get("courses")  # type: Optional[List[str]]
            course_runs = req.get("course_runs")  # type: Optional[List[str]]

            response_list.append(single_learner_cert_status(lms_user_id, username, course_ids, course_runs))

        return Response(
            status=status.HTTP_200_OK,
            data=response_list,
        )
