from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from credentials.apps.verifiable_credentials.issuance import status_list


class GenerateStatusListTestCase(TestCase):
    @patch.object(status_list, "issue_status_list")
    def test_generate_status_list(self, mock_issue_status_list):
        mock_issue_status_list.return_value = {}
        call_command("generate_status_list", "issuer_did")
        mock_issue_status_list.assert_called_once_with("issuer_did")
