from unittest import mock

from django.test import TestCase
from testfixtures import LogCapture

from credentials.apps.verifiable_credentials.issuance.main import CredentialIssuer

from .. import IssuanceException
from ..status_list import issue_status_list

LOGGER_NAME = "credentials.apps.verifiable_credentials.issuance.status_list"


class StatusListIssuanceTestCase(TestCase):
    @mock.patch("credentials.apps.verifiable_credentials.issuance.status_list.CredentialIssuer")
    def test_issue_status_list_sequence(self, mock_credential_issuer):
        mock_credential_issuer.return_value.issue.return_value = "dummy-credential"
        result = issue_status_list(issuer_id="mock-issuer")
        mock_credential_issuer.assert_called_once_with(issuance_uuid=mock_credential_issuer.init().uuid)
        mock_credential_issuer.return_value.issue.assert_called_once()
        self.assertEqual(result, "dummy-credential")

    @mock.patch.object(CredentialIssuer, "issue")
    def test_issue_status_list_failure(self, mock_issue):
        mock_issue.side_effect = IssuanceException
        with LogCapture() as log_capture:
            issue_status_list(issuer_id="test-issuer-id")
            log_capture.check(
                (LOGGER_NAME, "ERROR", "Status List generation failed: [test-issuer-id]"),
            )
