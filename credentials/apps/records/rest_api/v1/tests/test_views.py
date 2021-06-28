from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.records.rest_api.v1.serializers import ProgramSerializer
from credentials.apps.records.utils import get_user_program_data


class ProgramRecordsViewTests(SiteMixin, TestCase):
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
        self.program_cert = ProgramCertificateFactory.create(program_uuid=self.program.uuid, site=self.site)
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

    def test_deny_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get("/records/api/v1/program_records/")
        self.assertEqual(response.status_code, 401)

    def test_allow_authenticated_user(self):
        """Verify the endpoint requires an authenticated user."""
        self.client.logout()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        response = self.client.get("/records/api/v1/program_records/")
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        response = self.client.get("/records/api/v1/program_records/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["enrolled_programs"], self.serialize_program_records())
