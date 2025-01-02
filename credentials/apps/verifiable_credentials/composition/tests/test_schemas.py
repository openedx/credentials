from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

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
from credentials.apps.verifiable_credentials.composition.schemas import EducationalOccupationalCredentialSchema
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory


class EducationalOccupationalCredentialSchemaTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
        )
        self.course_certs = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program=self.program, program_uuid=self.program.uuid, site=self.site
        )
        self.course_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="coursecertificate"
        )
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        self.course_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.course_credential_content_type,
            credential=self.course_certs[0],
        )
        self.program_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert,
        )
        self.program_issuance_line = IssuanceLineFactory(
            user_credential=self.program_user_credential, subject_id="did:key:test"
        )
        self.course_issuance_line = IssuanceLineFactory(
            user_credential=self.course_user_credential, subject_id="did:key:test"
        )

    def test_to_representation_program(self):
        data = EducationalOccupationalCredentialSchema(self.program_issuance_line).data

        assert data["id"] == "EducationalOccupationalCredential"
        assert data["name"] == self.program_cert.title
        assert data["description"] == str(self.program_user_credential.uuid)
        assert data["program"]["id"] == "EducationalOccupationalProgram"
        assert data["program"]["name"] == self.program.title
        assert data["program"]["description"] == str(self.program.uuid)

    def test_to_representation_course(self):
        data = EducationalOccupationalCredentialSchema(self.course_issuance_line).data

        assert data["id"] == "EducationalOccupationalCredential"
        assert data["name"] == self.course_certs[0].title
        assert data["description"] == str(self.course_user_credential.uuid)
        assert data["course"]["id"] == "Course"
        assert data["course"]["name"] == self.course.title
        assert data["course"]["courseCode"] == self.course_certs[0].course_id
