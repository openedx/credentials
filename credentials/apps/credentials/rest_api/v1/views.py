import logging
import json

from django.apps import apps
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from credentials.apps.core.models import User
from credentials.apps.records.models import UserGrade
from credentials.apps.records.utils import get_credentials

log = logging.getLogger(__name__)

class LearnerCertificateStatusView(APIView):


    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        """
        **POST Parameters**

        A POST request must include one of "lms_user_id" or "username", 
        and it can have one or both of a list of course 
        uuids and/or a program uuid.

        {
            "lms_user_id": "lms_id",
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
        }        """
        lms_user_id = request.data.get("lms_user_id")
        username = request.data.get("username")

        #only one of username or lms_user_id can be used
        if (username and lms_user_id) or not (username or lms_user_id):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        if username:
            user = User.objects.get(username = username)
            print("lms_user_id:", user.lms_user_id)
        
        if lms_user_id:
            user = User.objects.get(lms_user_id = lms_user_id)
            if not user:
                # we don't have the user mapped to a lms_user_id
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            username = user.username

        course_ids = request.data.get("courses")

        #get the list of records for the user
        course_credentials, program_credentials = get_credentials(username)

        courses = list()
        for credential in course_credentials:
            if str(credential.credential.course_run.course.uuid) in course_ids:
                grade = UserGrade.objects.get(username=username, 
                                      course_run = credential.credential.course_run)
                cred_status = {
                    "course_uuid": str(credential.credential.course_run.course.uuid),
                    "course_run": 
                        { "uuid": str(credential.credential.course_run.uuid),
                          "key": credential.credential.course_run.key,
                        },
                    # alternate structure for course:
                    #"course": {
                    #    "uuid": str(credential.credential.course_run.course.uuid),
                    #    "title": credential.credential.course_run.course.title,
                    #    "key": credential.credential.course_run.course.key,
                    #},
                    
                    "status": credential.status,
                    "type": credential.credential.certificate_type,
                    "certificate_available_date": credential.credential.certificate_available_date,
                    "grade": grade.letter_grade,
                }
                courses.append(cred_status)

            else:
                print("uuid", credential.credential.course_run.course.uuid, "not in")
                print(course_ids)

        return Response(
            status=status.HTTP_200_OK,
            data={"lms_user_id": lms_user_id, 
                  "username": username,
                  "status": courses},
        )



