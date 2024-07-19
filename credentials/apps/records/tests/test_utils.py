import urllib
from logging import DEBUG

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from credentials.apps.catalog.data import ProgramStatus
from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    PathwayFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.data import UserCredentialStatus
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.models import ProgramCertRecord
from credentials.apps.records.tests.factories import ProgramCertRecordFactory, UserCreditPathwayFactory
from credentials.apps.records.tests.utils import dump_random_state
from credentials.apps.records.utils import (
    _course_credentials_to_course_runs,
    get_credentials,
    get_user_program_data,
    send_updated_emails_for_program,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UpdatedProgramEmailTests(SiteMixin, TestCase):
    """Tests for sending an update"""

    USERNAME = "test-records-user"

    def setUp(self):
        super().setUp()
        dump_random_state()
        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)
        self.pathway = PathwayFactory(site=self.site, programs=[self.program])
        self.pc = ProgramCertificateFactory(
            site=self.site,
            program_uuid=self.program.uuid,
            program=self.program,
        )
        self.pcr = ProgramCertRecordFactory(program=self.program, user=self.user)
        self.data = {"username": self.USERNAME, "pathway_id": self.pathway.id}
        self.url = reverse("records:share_program", kwargs={"uuid": self.program.uuid.hex})
        self.request = APIRequestFactory().get("/")

        mail.outbox = []

    def test_send_updated_email_when_program_finished(self):
        """
        Test that an additional updated email will be sent
        """
        # Mock sending an email to the partner
        UserCreditPathwayFactory(user=self.user, pathway=self.pathway, status=UserCreditPathwayStatus.SENT)
        self.assertEqual(0, len(mail.outbox))

        send_updated_emails_for_program(self.request, self.USERNAME, self.pc)

        # Check that another email was sent
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        record_path = reverse("records:public_programs", kwargs={"uuid": self.pcr.uuid.hex})
        expected_record_link = self.request.build_absolute_uri(record_path)
        expected_csv_link = urllib.parse.urljoin(expected_record_link, "csv")
        self.assertIn(self.program.title + " Updated Credit Request for", email.subject)
        self.assertIn(expected_record_link, email.body)
        self.assertIn(expected_csv_link, email.body)

    def test_skip_if_user_has_no_program_certificate(self):
        """Verify that if the user has no program certificate, we do nothing."""
        # Mock sending an email to the partner
        UserCreditPathwayFactory(user=self.user, pathway=self.pathway, status=UserCreditPathwayStatus.SENT)
        self.assertEqual(0, len(mail.outbox))

        # remover the fixture ProgramCertRecord
        ProgramCertRecord.objects.get(program=self.program, user=self.user).delete()

        with self.assertLogs(level=DEBUG) as cm:
            send_updated_emails_for_program(self.request, self.USERNAME, self.pc)
        self.assertRegex(cm.output[0], r".*ProgramCertRecord for user_uuid .*, program_uuid .* does not exist")

        # Check no other email was sent
        self.assertEqual(0, len(mail.outbox))

    def test_no_previous_email_sent(self):
        """
        Test that no additional email is sent if the user hasn't previously sent one
        """
        self.assertEqual(0, len(mail.outbox))

        send_updated_emails_for_program(self.request, self.USERNAME, self.pc)

        # Check that no email was sent
        self.assertEqual(0, len(mail.outbox))


class CourseCredentialsToCourseRunsTests(SiteMixin, TestCase):
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
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program_uuid=self.program.uuid,
            site=self.site,
            program=self.program,
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
        self.course_runs2 = None
        self.course_certs2 = None
        self.course_user_credentials2 = None

    def test_course_credentials_to_course_runs_zero(self):
        for course_cert in self.course_certs:
            course_cert.delete()
        result = _course_credentials_to_course_runs(self.site, self.course_user_credentials)
        assert len(result) == 0

    def test_course_credentials_to_course_runs_one_awarded(self):
        self.course_runs2 = CourseRunFactory.create_batch(1, course=self.course)
        self.course_certs2 = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs2
        ]
        self.course_user_credentials2 = [
            UserCredentialFactory.create(
                username=self.user.username,
                credential_content_type=self.course_credential_content_type,
                credential=course_cert,
            )
            for course_cert in self.course_certs2
        ]
        result = _course_credentials_to_course_runs(self.site, self.course_user_credentials2)
        assert result[0] == self.course_runs2[0]

    def test_course_credentials_to_course_runs_one_revoked(self):
        self.course_runs2 = CourseRunFactory.create_batch(1, course=self.course)
        self.course_certs2 = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs2
        ]
        self.course_user_credentials2 = [
            UserCredentialFactory.create(
                username=self.user.username,
                credential_content_type=self.course_credential_content_type,
                credential=course_cert,
                status=UserCredentialStatus.REVOKED.value,
            )
            for course_cert in self.course_certs2
        ]
        result = _course_credentials_to_course_runs(self.site, self.course_user_credentials2)
        assert len(result) == 0

    def test_course_credentials_to_course_runs_multiple(self):
        result = _course_credentials_to_course_runs(self.site, self.course_user_credentials)
        assert len(result) == 2
        assert result[0] == self.course_runs[0]
        assert result[1] == self.course_runs[1]


class GetCredentialsTests(SiteMixin, TestCase):

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
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program_uuid=self.program.uuid,
            site=self.site,
            program=self.program,
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

    def test_get_credentials_both_empty(self):
        """Verifies that empty sets are returned when there are no course or program certificates"""
        for course_cert in self.course_certs:
            course_cert.delete()
        self.program_cert.delete()
        course_results, program_results = get_credentials(self.user.username)
        assert course_results == []
        assert program_results == []

    def test_get_credentials_course_only(self):
        """Verify that the correct results are returned when there are course certificates
        but not program certificates"""
        self.program_cert.delete()
        course_results, program_results = get_credentials(self.user.username)
        assert course_results == self.course_user_credentials
        assert program_results == []

    def test_get_credentials_both_course_and_program(self):
        course_results, program_results = get_credentials(self.user.username)
        assert course_results == self.course_user_credentials
        assert program_results[0] == self.program_user_credential


class GetProgramDataTests(SiteMixin, TestCase):
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
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program_uuid=self.program.uuid,
            site=self.site,
            program=self.program,
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
        self.program2 = None
        self.program_cert2 = None
        self.program_user_credential2 = None

    def test_get_user_program_data_empty_true(self):
        self.program2 = ProgramFactory(
            title="TestProgram2Empty", course_runs=None, authoring_organizations=self.orgs, site=self.site
        )
        result = get_user_program_data(self.user.username, self.site, include_empty_programs=True)
        assert result[1]["empty"]

    def test_get_user_program_data_not_completed(self):
        self.program_user_credential.delete()
        result = get_user_program_data(self.user.username, self.site)
        assert not result[0]["completed"]

    def test_get_user_program_data_include_retired_programs_false(self):
        self.program2 = ProgramFactory(
            title="TestProgram2",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
            status=ProgramStatus.RETIRED.value,
        )
        self.program_cert2 = ProgramCertificateFactory.create(
            program_uuid=self.program2.uuid,
            site=self.site,
            program=self.program2,
        )
        self.program_user_credential2 = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert2,
        )
        result = get_user_program_data(self.user.username, self.site, include_retired_programs=False)
        assert len(result) == 1
        assert result[0]["name"] == self.program.title
        assert result[0]["uuid"] == str(self.program.uuid).replace("-", "")
        assert result[0]["completed"]
        assert not result[0]["empty"]

    def test_get_user_program_data_include_retired_programs_true(self):
        self.program2 = ProgramFactory(
            title="TestProgram2",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
            status=ProgramStatus.RETIRED.value,
        )
        self.program_cert2 = ProgramCertificateFactory.create(
            program_uuid=self.program2.uuid,
            site=self.site,
            program=self.program2,
        )
        self.program_user_credential2 = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert2,
        )
        result = get_user_program_data(self.user.username, self.site, include_retired_programs=True)
        assert len(result) == 2
        assert result[0]["name"] == self.program.title
        assert result[0]["uuid"] == str(self.program.uuid).replace("-", "")
        assert result[0]["completed"]
        assert not result[0]["empty"]
        assert result[1]["name"] == self.program2.title
        assert result[1]["uuid"] == str(self.program2.uuid).replace("-", "")
        assert result[1]["completed"]
        assert not result[1]["empty"]

    def test_get_user_program_data_zero_programs(self):
        self.program_cert.delete()
        self.program.delete()
        self.program_user_credential.delete()
        result = get_user_program_data(self.user.username, self.site)
        assert result == []

    def test_get_user_program_data_one_program(self):
        result = get_user_program_data(self.user.username, self.site)
        assert result[0]["name"] == self.program.title
        assert result[0]["uuid"] == str(self.program.uuid).replace("-", "")
        assert result[0]["completed"]
        assert not result[0]["empty"]

    def test_get_user_program_data_multiple_programs(self):
        self.program2 = ProgramFactory(
            title="TestProgram2", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.program_cert2 = ProgramCertificateFactory.create(
            program_uuid=self.program2.uuid,
            site=self.site,
            program=self.program2,
        )
        self.program_user_credential2 = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert2,
        )
        result = get_user_program_data(self.user.username, self.site)
        assert result[0]["name"] == self.program.title
        assert result[0]["uuid"] == str(self.program.uuid).replace("-", "")
        assert result[0]["completed"]
        assert not result[0]["empty"]
        assert result[1]["name"] == self.program2.title
        assert result[1]["uuid"] == str(self.program2.uuid).replace("-", "")
        assert result[1]["completed"]
        assert not result[1]["empty"]
