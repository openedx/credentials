import logging

from django.contrib.auth import get_user_model
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

    def post(self, request):
        """
        **POST Parameters**

        A POST request must include one of "lms_user_id" or "username",
        and a list of course uuids, course_runs, or a mix of both.
        (or a program uuid, in a future version)

        {
            "lms_user_id": <lms_id>,
            "courses": [
                "course_uuid1",
                "course_uuid2"
                ...
            ],
            "course_runs": [
                "course_run_uuid1",
                "course_run_key2",
                ...
            ]
        }

        **POST Response Values**

        The request will return a 200 with a list of learner cert statuses.

        {
            "lms_user_id": 3,
            "username": "edx",
            "status": [
                {
                    "course_uuid": "8759ceb8-7112-4b48-a9b4-8a9a69fdad51",
                    "course_run": {
                        "uuid": "0e63eeea-f957-4d38-884a-bf7af5af6155",
                        "key": "course-v1:edX+TK-100+2T2022"
                    },
                    "status": "awarded",
                    "type": "verified",
                    "certificate_available_date": null,
                    "grade": {
                        "letter_grade": "Pass",
                        "percent_grade": 75.0,
                        "verified": true
                        }
                },
                {
                    "course_uuid": "d81fce24-c0e3-49cc-b375-51a02c79aa9d",
                    "course_run": {
                        "uuid": "b4a38fe1-93b6-4fa6-a834-a656bcf9e75c",
                        "key": "course-v1:edX+CRYPT101+1T2023"
                    },
                    "status": "awarded",
                    "type": "verified",
                    "certificate_available_date": null,
                    "grade": {
                        "letter_grade": "Pass",
                        "percent_grade": 70.5,
                        "verified": true
                        }
                }
            ]
        }"""
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
