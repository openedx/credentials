import json
import logging

from django.apps import apps
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from credentials.apps.core.models import User
from credentials.apps.credentials.rest_api.v1.permissions import CanGetLearnerStatus
from credentials.apps.records.models import UserGrade
from credentials.apps.records.utils import get_credentials


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
        and it can have one or both of a list of course
        uuids and/or a program uuid.

        {
            "lms_user_id": <lms_id>,
            "courses": [
                "uuid1",
                "uuid2"
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
                    "grade": "Pass"
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
                    "grade": "Pass"
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

        try:
            if username:
                user = User.objects.get(username=username)
                lms_user_id = user.lms_user_id
            else:
                user = User.objects.get(lms_user_id=lms_user_id)
                username = user.username
        except User.DoesNotExist:
            # we don't have the user in the system
            return Response(status=status.HTTP_404_NOT_FOUND)

        course_ids = request.data.get("courses")

        # get the list of records for the user
        course_credentials, program_credentials = get_credentials(username)

        courses = list()
        for credential in course_credentials:
            if str(credential.credential.course_run.course.uuid) in course_ids:
                # we don't always have the grade, so defend for missing it
                try:
                    grade = UserGrade.objects.get(username=username, course_run=credential.credential.course_run)
                    letter_grade = grade.letter_grade
                except UserGrade.DoesNotExist:
                    letter_grade = None

                cred_status = {
                    "course_uuid": str(credential.credential.course_run.course.uuid),
                    "course_run": {
                        "uuid": str(credential.credential.course_run.uuid),
                        "key": credential.credential.course_run.key,
                    },
                    "status": credential.status,
                    "type": credential.credential.certificate_type,
                    "certificate_available_date": credential.credential.certificate_available_date,
                    "grade": letter_grade,
                }
                courses.append(cred_status)

        return Response(
            status=status.HTTP_200_OK,
            data={"lms_user_id": lms_user_id, "username": username, "status": courses},
        )
