import base64

import pytest
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
from credentials.apps.verifiable_credentials.utils import (
    capitalize_first,
    generate_base64_qr_code,
    get_user_program_credentials_data,
)


class GetProgramCertificatesTests(SiteMixin, TestCase):
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

    def test_get_user_program_credentials_data_not_completed(self):
        self.program_user_credential.delete()
        result = get_user_program_credentials_data(self.user.username)
        assert result == []

    def test_get_user_program_credentials_data_zero_programs(self):
        self.program_cert.delete()
        self.program.delete()
        self.program_user_credential.delete()
        result = get_user_program_credentials_data(self.user.username)
        assert result == []

    def test_get_user_program_credentials_data_one_program(self):
        result = get_user_program_credentials_data(self.user.username)
        assert result[0]["uuid"] == str(self.program_user_credential.uuid).replace("-", "")
        assert result[0]["status"] == self.program_user_credential.status
        assert result[0]["username"] == self.program_user_credential.username
        assert result[0]["download_url"] == self.program_user_credential.download_url
        assert result[0]["credential_id"] == self.program_user_credential.credential_id
        assert result[0]["program_uuid"] == str(self.program_user_credential.credential.program_uuid).replace("-", "")
        assert result[0]["program_title"] == self.program_user_credential.credential.program.title

    def test_get_user_program_credentials_data_multiple_programs(self):
        self.program2 = ProgramFactory(
            title="TestProgram2",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
        )
        self.program_cert2 = ProgramCertificateFactory.create(
            program=self.program2, program_uuid=self.program2.uuid, site=self.site
        )
        self.program_user_credential2 = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert2,
        )
        result = get_user_program_credentials_data(self.user.username)
        assert result[0]["uuid"] == str(self.program_user_credential.uuid).replace("-", "")
        assert result[0]["status"] == self.program_user_credential.status
        assert result[0]["username"] == self.program_user_credential.username
        assert result[0]["download_url"] == self.program_user_credential.download_url
        assert result[0]["credential_id"] == self.program_user_credential.credential_id
        assert result[0]["program_uuid"] == str(self.program_user_credential.credential.program_uuid).replace("-", "")
        assert result[0]["program_title"] == self.program_user_credential.credential.program.title

        assert result[1]["uuid"] == str(self.program_user_credential2.uuid).replace("-", "")
        assert result[1]["status"] == self.program_user_credential2.status
        assert result[1]["username"] == self.program_user_credential2.username
        assert result[1]["download_url"] == self.program_user_credential2.download_url
        assert result[1]["credential_id"] == self.program_user_credential2.credential_id
        assert result[1]["program_uuid"] == str(self.program_user_credential2.credential.program_uuid).replace("-", "")
        assert result[1]["program_title"] == self.program_user_credential2.credential.program.title


class TestGenerateBase64QRCode(TestCase):
    def test_correct_output_format(self):
        result = generate_base64_qr_code("Test Text")
        self.assertIsInstance(result, str)

        decoded_result = base64.b64decode(result)
        self.assertIsInstance(decoded_result, bytes)


@pytest.mark.parametrize(
    "test_input,expected",
    [("open edX", "Open edX"), ("open edx", "Open edx"), ("", ""), (None, None), (1, 1)],
)
def test_capitalize_first(test_input, expected):
    assert capitalize_first(test_input) == expected
