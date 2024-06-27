from unittest.mock import patch

import ddt
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from edx_toggles.toggles.testutils import override_waffle_switch
from testfixtures import LogCapture

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.api import (
    _get_course_run,
    _update_or_create_credential,
    create_course_cert_config,
    get_course_cert_config,
    get_course_certificates_with_ids,
    get_program_certificates_with_ids,
    get_user_credentials_by_content_type,
    process_course_credential_update,
)
from credentials.apps.credentials.data import UserCredentialStatus
from credentials.apps.credentials.models import CourseCertificate, ProgramCertificate, UserCredential
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
                course_run=course_run,
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


@override_waffle_switch(settings.USE_CERTIFICATE_AVAILABLE_DATE, active=True)
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

    def test_get_user_credentials_by_content_type_when_no_valid_types(self):
        """get_user_credentials_by_content_type returns empty when there's no creds of the type"""
        course_cert_content_types = ContentType.objects.filter(app_label="credentials", model__in=["goldstar"])
        for course_user_credential in self.course_user_credentials:
            course_user_credential.delete()
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 0

    def test_get_user_credentials_by_content_type_when_no_creds(self):
        """get_user_credentials_by_content_type returns empty when there's no applicable creds"""
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
        """get_user_credentials_by_content_type returns course certificates when asked"""
        course_cert_content_types = ContentType.objects.filter(app_label="credentials", model__in=["coursecertificate"])
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 2
        assert result[0] == self.course_user_credentials[0]
        assert result[1] == self.course_user_credentials[1]

    def test_get_user_credentials_by_content_type_program_only(self):
        """get_user_credentials_by_content_type returns program certificates when asked"""
        course_cert_content_types = ContentType.objects.filter(
            app_label="credentials", model__in=["programcertificate"]
        )
        result = get_user_credentials_by_content_type(
            self.user.username, course_cert_content_types, UserCredentialStatus.AWARDED.value
        )
        assert len(result) == 1
        assert result[0] == self.program_user_credential

    def test_get_user_credentials_by_content_type_course_and_program(self):
        """get_user_credentials_by_content_type returns courses and programs when asked"""
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


class GetCourseRunTests(SiteMixin, TestCase):
    """
    Tests for the `_get_course_run` utility function.
    """

    def test_get_existing_course_run(self):
        """
        Happy path. This test ensures that we can retrieve a course run instance when using the `_get_course_run`
        function.
        """
        course_run = CourseRunFactory()

        expected_message = f"Attempting to retrieve course run with key [{course_run.key}]"

        with LogCapture() as log:
            result = _get_course_run(course_run.key)

        assert result.key == course_run.key
        assert result.id == course_run.id
        assert log.records[0].msg == expected_message

    def test_get_course_run_dne(self):
        """
        This test verifies the expected behavior of the `_get_course_run` function when we cannot find the course run
        requested.
        """
        course_run_key = "blub/blub/glub"
        expected_messages = [
            f"Attempting to retrieve course run with key [{course_run_key}]",
            f"Could not retrieve a course run with key [{course_run_key}]",
        ]

        with LogCapture() as log:
            result = _get_course_run(course_run_key)

        assert result is None
        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()


@ddt.ddt
class UpdateOrCreateCredentialTests(SiteMixin, TestCase):
    """
    Tests for the `_update_or_create_credential` utility function.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.org = OrganizationFactory(site=self.site)
        self.course = CourseFactory.create(site=self.site)
        self.course_run = CourseRunFactory.create(course=self.course)
        self.course_cert_config = CourseCertificateFactory.create(
            course_id=self.course_run.key, course_run=self.course_run, site=self.site
        )
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=[self.course_run], authoring_organizations=[self.org], site=self.site
        )
        self.program_cert_config = ProgramCertificateFactory.create(program_uuid=self.program.uuid, site=self.site)

    @ddt.data(
        [CourseCertificate, UserCredentialStatus.AWARDED],
        [CourseCertificate, UserCredentialStatus.REVOKED],
        [ProgramCertificate, UserCredentialStatus.AWARDED],
        [ProgramCertificate, UserCredentialStatus.REVOKED],
    )
    @ddt.unpack
    def test_create_credential(self, credential_type, cert_status):
        """
        Happy path. This test verifies the functionality of the `_update_or_create_credentials` utility function.
        Ensures that we can create a UserCredential of the appropriate type based on the data passed to the function.
        """
        with LogCapture() as log:
            if credential_type is CourseCertificate:
                cert, created = _update_or_create_credential(
                    self.user.username, credential_type, self.course_cert_config.id, cert_status
                )
            else:
                cert, created = _update_or_create_credential(
                    self.user.username, credential_type, self.program_cert_config.id, cert_status
                )

        expected_message = (
            f"Processed credential update for user [{self.user.username}] with status [{cert_status}]. UUID: "
            f"[{cert.uuid}], created: [{created}]"
        )

        assert cert.status == cert_status
        assert log.records[0].msg == expected_message

    def test_create_credential_exception_occurs(self):
        """
        This test verifies the behavior of the `_update_or_create_credentials` utility function when an exception
        occurs.
        """
        with LogCapture() as log:
            cert, created = _update_or_create_credential(
                self.user.username, None, self.course_cert_config.id, UserCredentialStatus.AWARDED
            )

        expected_message = (
            f"Error occurred processing a credential with credential_id [{self.course_cert_config.id}] for user "
            f"[{self.user.username}]"
        )

        assert cert is None
        assert created is None
        assert log.records[0].msg == expected_message


class GetOrCreateCertConfigTests(SiteMixin, TestCase):
    """
    Tests for the the Python API functions that deal with retrieving or creating course certificate configurations.
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(site=self.site)
        self.course_run = CourseRunFactory.create(course=self.course)

    def test_get_course_cert_config(self):
        """
        Happy path. This test case verifies that we can retrieve an existing CourseCertificate instance when calling the
        `get_course_cert_config` function.
        """
        course_cert_config = CourseCertificateFactory.create(
            course_id=self.course_run.key, course_run=self.course_run, site=self.site
        )

        expected_message = (
            f"Attempting to retrieve the course certificate configuration for course run [{self.course_run.key}]"
        )

        with LogCapture() as log:
            course_cert = get_course_cert_config(self.course_run, "honor")

        assert course_cert.course_id == self.course_run.key
        assert course_cert.course_run == self.course_run
        assert course_cert.id == course_cert_config.id
        assert log.records[0].msg == expected_message

    @patch("credentials.apps.credentials.api.create_course_cert_config")
    def test_get_course_cert_config_dne(self, mock_create):
        """
        This test case verifies the behavior of the `get_course_cert_config` function when the requested course
        certificate does not exist.
        """
        expected_messages = [
            f"Attempting to retrieve the course certificate configuration for course run [{self.course_run.key}]",
            f"A course certificate configuration could not be found for course run [{self.course_run.key}]",
        ]

        with LogCapture() as log:
            course_cert = get_course_cert_config(self.course_run, "honor")

        assert course_cert is None
        mock_create.assert_not_called()
        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()

    @patch("credentials.apps.credentials.api.create_course_cert_config")
    def test_get_course_cert_config_dne_attempt_create(self, mock_create):
        """
        This test case verifies the behavior of the `get_course_cert_config` function when the requested course
        certificate does not exist. It also verifies that we will attempt to create the course certificate instance.
        """
        expected_messages = [
            f"Attempting to retrieve the course certificate configuration for course run [{self.course_run.key}]",
            f"A course certificate configuration could not be found for course run [{self.course_run.key}]",
        ]

        with LogCapture() as log:
            get_course_cert_config(self.course_run, "honor", create=True)

        mock_create.assert_called_once_with(self.course_run, self.site, "honor")
        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()

    def test_create_course_cert_config(self):
        """
        Happy path. This test verifies that we can create a CourseCertificate instance with the information provided by
        the function call using the `create_course_cert_config` function.
        """
        expected_message = f"Creating a course certificate configuration for course run [{self.course_run.key}]"

        with LogCapture() as log:
            course_cert = create_course_cert_config(self.course_run, self.site, "verified")

        assert course_cert.course_id == self.course_run.key
        assert course_cert.course_run == self.course_run
        assert course_cert.certificate_type == "verified"
        assert log.records[0].msg == expected_message

    def test_create_course_cert_config_exception_occurs(self):
        """
        This test verifies the functionality of the `create_course_cert_config` function when we fail to create a course
        cert configuration from the data provided.
        """
        expected_messages = [
            f"Creating a course certificate configuration for course run [{self.course_run.key}]",
            f"Error occurred creating a CourseCertificate configuration for course run [{self.course_run.key}]",
        ]

        with LogCapture() as log:
            course_cert = create_course_cert_config(self.course_run, self.site, None)

        assert course_cert is None
        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()


class ProcessCourseCredentialUpdateTests(SiteMixin, TestCase):
    """
    Test cases for the `process_course_credential_update` utility function.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.org = OrganizationFactory(site=self.site)
        self.course = CourseFactory.create(site=self.site)
        self.course_run = CourseRunFactory.create(course=self.course)

    def test_award_course_credential(self):
        """
        Happy path. Verifies that we can award a UserCredential to a learner from event data consumed from the Event
        Bus.
        """
        course_cert_config = CourseCertificateFactory.create(
            course_id=self.course_run.key, course_run=self.course_run, site=self.site
        )

        process_course_credential_update(self.user, self.course_run.key, "honor", "awarded")
        credential = UserCredential.objects.get(username=self.user.username, credential_id=course_cert_config.id)

        assert credential.username == self.user.username
        assert credential.credential_id == course_cert_config.id
        assert credential.status == "awarded"
        # 12 is the content type for "Course Certificate"
        assert credential.credential_content_type_id == 12

    def test_revoke_course_credential(self):
        """
        Happy path. Verifies that we can revoke a course credential from a user after consuming an event from the Event
        Bus.
        """
        course_credential_content_type = ContentType.objects.get(app_label="credentials", model="coursecertificate")
        course_cert_config = CourseCertificateFactory.create(
            course_id=self.course_run.key, course_run=self.course_run, site=self.site
        )
        credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=course_credential_content_type,
            credential=course_cert_config,
            status=UserCredential.REVOKED,
        )
        process_course_credential_update(self.user, self.course_run.key, "honor", "revoked")
        credential = UserCredential.objects.get(username=self.user.username, credential_id=course_cert_config.id)

        assert credential.username == self.user.username
        assert credential.credential_id == course_cert_config.id
        assert credential.status == "revoked"
        # 12 is the content type for "Course Certificate"
        assert credential.credential_content_type_id == 12

    def test_update_existing_cert(self):
        """
        A unit test that verifies we can update an existing certificate record.
        """
        course_credential_content_type = ContentType.objects.get(app_label="credentials", model="coursecertificate")
        course_cert_config = CourseCertificateFactory.create(
            course_id=self.course_run.key, course_run=self.course_run, site=self.site
        )
        credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=course_credential_content_type,
            credential=course_cert_config,
            status=UserCredential.REVOKED,
        )
        expected_message = (
            f"Processed credential update for user [{self.user.username}] with status [{UserCredential.AWARDED}]. "
            f"UUID: [{credential.uuid}], created: [False]"
        )

        with LogCapture() as logs:
            process_course_credential_update(self.user, self.course_run.key, "honor", "awarded")

        credential = UserCredential.objects.get(
            username=self.user.username,
            credential_id=course_cert_config.id,
            credential_content_type=course_credential_content_type,
        )
        log_messages = [log.msg for log in logs.records]

        assert credential.username == self.user.username
        assert credential.credential_id == course_cert_config.id
        assert credential.status == "awarded"
        assert expected_message in log_messages

    def test_award_course_cert_no_course_run(self):
        """
        This test case verifies the expected behavior of the `process_course_certificate_update` function if a course
        run received from an event does not exist in Credentials.
        """
        course_run_key = "course-v1:lol-doesnt-exist"
        expected_messages = [
            f"Attempting to retrieve course run with key [{course_run_key}]",
            f"Could not retrieve a course run with key [{course_run_key}]",
            f"Error updating credential for user [{self.user.id}] with status [awarded]. A course run could not be "
            f"found with key [{course_run_key}]",
        ]

        with LogCapture() as log:
            process_course_credential_update(self.user, course_run_key, "honor", "awarded")

        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()

    def test_award_course_cert_no_course_certificate(self):
        """
        This test case verifies the expected behavior of the `process_course_certificate_update` function if a course
        cert configuration doesn't exist for the course run.
        """
        process_course_credential_update(self.user, self.course_run.key, "honor", "awarded")
        course_cert_config = CourseCertificate.objects.get(course_run=self.course_run, certificate_type="honor")
        credential = UserCredential.objects.get(username=self.user.username, credential_id=course_cert_config.id)
        assert credential.username == self.user.username
        assert credential.credential_id == course_cert_config.id
        assert credential.status == "awarded"
        # 12 is the content type for "Course Certificate"
        assert credential.credential_content_type_id == 12

    def test_award_course_cert_no_course_certificate_exception_occurs(self):
        """
        This test case verifies the expected behavior of the `process_course_certificate_update` function if a course
        cert configuration doesn't exist, but an exception occurs when we try to create it on the fly.
        """
        expected_messages = [
            f"Attempting to retrieve course run with key [{self.course_run.key}]",
            f"Attempting to retrieve the course certificate configuration for course run [{self.course_run.key}]",
            f"A course certificate configuration could not be found for course run [{self.course_run.key}]",
            f"Creating a course certificate configuration for course run [{self.course_run.key}]",
            f"Error occurred creating a CourseCertificate configuration for course run [{self.course_run.key}]",
            f"Error updating credential for user [{self.user.id}] in course run [{self.course_run.key}] with status "
            "[awarded]. A course certificate configuration could not be found or created.",
        ]

        with LogCapture() as log:
            process_course_credential_update(self.user, self.course_run.key, None, "awarded")

        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()
