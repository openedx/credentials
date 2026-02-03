import json
import uuid
from unittest import mock

import didkit
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from testfixtures import LogCapture

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory
from credentials.apps.verifiable_credentials.issuance.main import CredentialIssuer
from credentials.apps.verifiable_credentials.issuance.tests.factories import (
    IssuanceConfigurationFactory,
    IssuanceLineFactory,
)
from credentials.apps.verifiable_credentials.storages.learner_credential_wallet import LCWallet

from .. import IssuanceException

LOGGER_NAME = "credentials.apps.verifiable_credentials.issuance.main"


class MainIssuanceTestCase(SiteMixin, TestCase):
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
        self.issuance_line = IssuanceLineFactory.create(
            user_credential=self.program_user_credential,
            status_index=5,
            storage_id=LCWallet.ID,
        )
        self.issuance_configuration = IssuanceConfigurationFactory.create(
            issuer_id=self.issuance_line.issuer_id,
        )
        self.inactive_issuance_line = IssuanceLineFactory.create(
            user_credential=self.program_user_credential, status_index=6, status=UserCredentialStatus.REVOKED
        )

    def test_pickup_issuance_line_isnt_exists(self):
        fake_uuid = uuid.uuid4()
        with self.assertRaisesMessage(ValidationError, f"Couldn't find such issuance line: [{fake_uuid}]"):
            CredentialIssuer(issuance_uuid=fake_uuid)

    def test_pickup_issuance_line_inactive(self):
        with self.assertRaisesMessage(
            ValidationError,
            f"Seems credential isn't active anymore: [{self.inactive_issuance_line.user_credential.uuid}]",
        ):
            CredentialIssuer(issuance_uuid=self.inactive_issuance_line.uuid)

    def test_init_class_with_correct_issuance_line(self):
        credential_issuer = CredentialIssuer(issuance_uuid=self.issuance_line.uuid)
        self.assertEqual(credential_issuer._issuance_line, self.issuance_line)  # pylint: disable=protected-access
        self.assertEqual(credential_issuer._storage, self.issuance_line.storage)  # pylint: disable=protected-access

    def test_init_class_with_correct_issuance_line_with_correct_data(self):
        data = {"holder": "test-holder-id"}
        credential_issuer = CredentialIssuer(issuance_uuid=self.issuance_line.uuid, data=data)
        self.assertEqual(
            credential_issuer._issuance_line.subject_id, "test-holder-id"  # pylint: disable=protected-access
        )

    def test_init_issuance(self):
        issuance_line = CredentialIssuer.init(
            storage_id=LCWallet.ID,
            user_credential=self.program_user_credential,
            issuer_id="another-issuer-id",
        )

        self.assertEqual(issuance_line.user_credential, self.program_user_credential)
        self.assertFalse(issuance_line.processed)
        self.assertEqual(issuance_line.issuer_id, "another-issuer-id")
        self.assertEqual(issuance_line.status, self.program_user_credential.status)
        self.assertEqual(issuance_line.data_model_id, LCWallet.PREFERRED_DATA_MODEL.ID)
        self.assertEqual(issuance_line.status_index, 0)

    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.didkit_issue_credential")
    def test_sign(self, mock_didkit_issue_credential):
        mock_didkit_issue_credential.return_value = {"test-property": "test-value"}
        signed_credential = CredentialIssuer(issuance_uuid=self.issuance_line.uuid).sign({})
        self.assertEqual(signed_credential, {"test-property": "test-value"})

    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.didkit_issue_credential")
    def test_sign_failure(self, mock_didkit_issue_credential):
        mock_didkit_issue_credential.side_effect = (
            didkit.DIDKitException
        )  # pylint: disable=no-member, useless-suppression
        with self.assertRaises(IssuanceException):
            CredentialIssuer(issuance_uuid=self.issuance_line.uuid).sign({})

        mock_didkit_issue_credential.side_effect = ValueError
        with self.assertRaises(IssuanceException):
            CredentialIssuer(issuance_uuid=self.issuance_line.uuid).sign({})

    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.didkit_verify_credential")
    def test_verify(self, mock_didkit_verify_credential):
        mock_didkit_verify_credential.return_value = {"result": "test-result"}
        with LogCapture() as log_capture:
            CredentialIssuer(issuance_uuid=self.issuance_line.uuid).verify({})
            log_capture.check(
                (LOGGER_NAME, "DEBUG", "Verifiable credential passed verifiacation: ({'result': 'test-result'})"),
            )

    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.CredentialIssuer.compose")
    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.CredentialIssuer.sign")
    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.CredentialIssuer.verify")
    @mock.patch("credentials.apps.verifiable_credentials.issuance.main.IssuanceLine.finalize")
    def test_issue_sequence(self, mock_finalize, mock_verify, mock_sign, mock_compose):
        mock_compose.return_value = {"credential": "composed"}
        mock_sign.return_value = json.dumps({"credential": "composed-and-signed"})

        result = CredentialIssuer(issuance_uuid=self.issuance_line.uuid).issue()

        mock_compose.assert_called_once()
        mock_sign.assert_called_once_with({"credential": "composed"})
        mock_verify.assert_called_once_with(json.dumps({"credential": "composed-and-signed"}))
        mock_finalize.assert_called_once()
        self.assertEqual(result, json.loads(json.dumps({"credential": "composed-and-signed"})))
