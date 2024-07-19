from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.records.api import get_program_details
from credentials.apps.records.rest_api.v1.serializers import ProgramRecordSerializer, ProgramSerializer
from credentials.apps.records.utils import get_user_program_data


class ProgramRecordsSerializerTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.course_certs = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program_uuid=self.program.uuid, site=self.site, program=self.program
        )
        self.course_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="coursecertificate"
        )
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        self.course_user_credentials = [
            UserCredentialFactory.create(
                username=self.user.username,
                credential_content_type=self.course_credential_content_type,
                credential=course_cert,
            )
            for course_cert in self.course_certs
        ]
        self.program_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert,
        )

    def serialize_program_records(self):
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get("/")
        return ProgramSerializer(
            get_user_program_data(
                self.user.username, self.site, include_empty_programs=False, include_retired_programs=True
            ),
            context={"request": request},
            many=True,
        ).data

    def serialize_program_record_details(self):
        url = "/" + str(self.program.uuid)
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get(url)
        return ProgramRecordSerializer(
            get_program_details(
                request_user=self.user, request_site=self.site, uuid=self.program.uuid, is_public=False
            ),
            context={"request": request},
        ).data

    def test_valid_data_zero_programs(self):
        """Verify the serializer produces an empty list if there are no programs"""
        self.program_cert.delete()
        self.program.delete()
        serializer = self.serialize_program_records()
        expected = []
        self.assertEqual(serializer, expected)

    def test_valid_data_no_program_cert(self):
        """Verify the endpoint connects if program completion is in-progress."""
        self.program_cert.delete()
        serializer = self.serialize_program_records()
        expected = {
            "name": "TestProgram1",
            "uuid": self.program.uuid,
            "partner": "TestOrg1, TestOrg2",
            "completed": False,
            "empty": False,
        }
        self.assertEqual(serializer[0]["name"], expected["name"])
        self.assertEqual(serializer[0]["uuid"], str(expected["uuid"]).replace("-", ""))
        self.assertEqual(serializer[0]["partner"], expected["partner"])
        self.assertEqual(serializer[0]["completed"], expected["completed"])
        self.assertEqual(serializer[0]["empty"], expected["empty"])

    def test_valid_data(self):
        serializer = self.serialize_program_records()
        expected = {
            "name": "TestProgram1",
            "uuid": self.program.uuid,
            "partner": "TestOrg1, TestOrg2",
            "completed": True,
            "empty": False,
        }
        self.assertEqual(serializer[0]["name"], expected["name"])
        self.assertEqual(serializer[0]["uuid"], str(expected["uuid"]).replace("-", ""))
        self.assertEqual(serializer[0]["partner"], expected["partner"])
        self.assertEqual(serializer[0]["completed"], expected["completed"])
        self.assertEqual(serializer[0]["empty"], expected["empty"])

    def test_valid_details_data(self):
        serializer = self.serialize_program_record_details()
        expected = {
            "record": {
                "learner": {"full_name": self.user.full_name, "username": self.user.username, "email": self.user.email},
                "program": {
                    "name": "TestProgram1",
                    "uuid": self.program.uuid,
                    "partner": "TestOrg1, TestOrg2",
                    "completed": True,
                    "empty": True,
                },
                "platform_name": self.site_configuration.platform_name,
                "grades": [
                    {
                        "name": "Test çօմɾʂҽ iJXceupiNcKb",
                        "school": "",
                        "attempts": 0,
                        "course_id": "",
                        "issue_date": "",
                        "percent_grade": 0.0,
                        "letter_grade": "",
                    },
                ],
                "pathways": [],
            },
            "is_public": False,
            "uuid": self.program.uuid,
            "records_help_url": self.site_configuration.records_help_url,
        }
        self.assertEqual(serializer["record"]["learner"]["full_name"], expected["record"]["learner"]["full_name"])
        self.assertEqual(serializer["record"]["learner"]["username"], expected["record"]["learner"]["username"])
        self.assertEqual(serializer["record"]["learner"]["email"], expected["record"]["learner"]["email"])
        self.assertEqual(serializer["record"]["program"]["name"], expected["record"]["program"]["name"])
        self.assertEqual(str(serializer["uuid"]).replace("-", ""), str(expected["uuid"]).replace("-", ""))
        self.assertEqual(serializer["record"]["program"]["school"], expected["record"]["program"]["partner"])
        self.assertEqual(serializer["record"]["program"]["completed"], expected["record"]["program"]["completed"])
        self.assertEqual(serializer["record"]["program"]["empty"], expected["record"]["program"]["empty"])
        self.assertEqual(serializer["record"]["platform_name"], expected["record"]["platform_name"])
        self.assertEqual(serializer["record"]["pathways"], expected["record"]["pathways"])
        self.assertEqual(serializer["is_public"], expected["is_public"])
        self.assertEqual(serializer["records_help_url"], expected["records_help_url"])
