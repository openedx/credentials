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
from credentials.apps.credentials.api import (
    get_course_certificates_with_ids,
    get_program_certificates_with_ids,
    get_user_credentials_by_content_type,
)
from credentials.apps.credentials.data import UserCredentialStatus
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)


class GetCourseCertificatesWithIdsTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.course_certs = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.course_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="coursecertificate"
        )
        self.course_user_credentials = [
            UserCredentialFactory.create(
                username=self.user.username,
                credential_content_type=self.course_credential_content_type,
                credential=course_cert,
            )
            for course_cert in self.course_certs
        ]

    def test_get_course_certificates_with_ids_zero(self):
        course_credential_ids = []
        result = get_course_certificates_with_ids(course_credential_ids, self.site)
        assert len(result) == 0

    def test_get_course_certificates_with_ids_one(self):
        course_credential_ids = [self.course_user_credentials[0].credential_id]
        result = get_course_certificates_with_ids(course_credential_ids, self.site)
        assert len(result) == 1
        assert result[0] == self.course_certs[0]

    def test_get_course_certificates_with_ids_multiple(self):
        course_credential_ids = [
            x.credential_id for x in self.course_user_credentials if x.status == UserCredentialStatus.AWARDED.value
        ]
        result = get_course_certificates_with_ids(course_credential_ids, self.site)
        assert len(result) == 2
        assert result[0] == self.course_certs[0]
        assert result[1] == self.course_certs[1]


class GetProgramCertificatesWithIdsTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.program_cert = ProgramCertificateFactory.create(program_uuid=self.program.uuid, site=self.site)
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        self.program_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert,
        )
        self.course2 = None
        self.course_runs2 = None
        self.program2 = None
        self.program_cert2 = None
        self.program_user_credential2 = None

    def test_get_program_certificates_with_ids_zero(self):
        program_credential_ids = []
        result = get_program_certificates_with_ids(program_credential_ids, self.site)
        assert len(result) == 0

    def test_get_program_certificates_with_ids_one(self):
        program_credential_ids = [self.program_user_credential.credential_id]
        result = get_program_certificates_with_ids(program_credential_ids, self.site)
        assert len(result) == 1
        assert result[0] == self.program_cert

    def test_get_program_certificates_with_ids_multiple(self):
        self.course2 = CourseFactory.create(site=self.site)
        self.course_runs2 = CourseRunFactory.create_batch(2, course=self.course2)
        self.program2 = ProgramFactory(
            title="TestProgram2", course_runs=self.course_runs2, authoring_organizations=self.orgs, site=self.site
        )
        self.program_cert2 = ProgramCertificateFactory.create(program_uuid=self.program2.uuid, site=self.site)
        self.program_user_credential2 = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert2,
        )
        program_credential_ids = [
            self.program_user_credential.credential_id,
            self.program_user_credential2.credential_id,
        ]
        result = get_program_certificates_with_ids(program_credential_ids, self.site)
        assert len(result) == 2
        assert result[0] == self.program_cert
        assert result[1] == self.program_cert2


class GetUserCredentialsByContentTypeTests(SiteMixin, TestCase):
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

    def test_get_user_credentials_by_content_type_zero(self):
        course_cert_content_types = ContentType.objects.filter(
            app_label="credentials", model__in=["coursecertificate", "programcertificate"]
        )
        self.program_user_credential.delete()
        for course_user_credential in self.course_user_credentials:
            course_user_credential.delete()
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 0

    def test_get_user_credentials_by_content_type_course_only(self):
        course_cert_content_types = ContentType.objects.filter(
            app_label="credentials", model__in=["coursecertificate", "programcertificate"]
        )
        self.program_user_credential.delete()
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 2
        assert result[0] == self.course_user_credentials[0]
        assert result[1] == self.course_user_credentials[1]

    def test_get_user_credentials_by_content_type_program_only(self):
        course_cert_content_types = ContentType.objects.filter(
            app_label="credentials", model__in=["coursecertificate", "programcertificate"]
        )
        for course_user_credential in self.course_user_credentials:
            course_user_credential.delete()
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 1
        assert result[0] == self.program_user_credential

    def test_get_user_credentials_by_content_type_course_and_program(self):
        course_cert_content_types = ContentType.objects.filter(
            app_label="credentials", model__in=["coursecertificate", "programcertificate"]
        )
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 3
        assert result[0] == self.course_user_credentials[0]
        assert result[1] == self.course_user_credentials[1]
        assert result[2] == self.program_user_credential
