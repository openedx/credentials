from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase


class GenerateIssuerCredentialsTestCase(TestCase):
    @patch("didkit.generate_ed25519_key")
    @patch("didkit.key_to_did")
    @patch("pprint.pprint")
    def test_handle_command(self, mock_pprint, mock_key_to_did, mock_generate_ed25519_key):
        mock_key = MagicMock()
        mock_generate_ed25519_key.return_value = mock_key
        mock_did = MagicMock()
        mock_key_to_did.return_value = mock_did

        call_command("generate_issuer_credentials")

        mock_generate_ed25519_key.assert_called_once()
        mock_key_to_did.assert_called_once_with(jwk=mock_key, method_pattern="key")
        mock_pprint.assert_called_once_with(
            {
                "private_key": mock_key,
                "did": mock_did,
            }
        )
