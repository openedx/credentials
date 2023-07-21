from unittest.mock import MagicMock, patch

from django.test import TestCase

from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory

from ..permissions import VerifiablePresentation


class VerifiablePresentationTestCase(TestCase):
    def setUp(self):
        self.permission = VerifiablePresentation()
        self.issuance_line = IssuanceLineFactory.create()

    def test_returns_false_if_proofPurpose_not_authentication(self):
        request = MagicMock(data={"proof": {"proofPurpose": "assertion"}})
        self.assertFalse(self.permission.has_permission(request, None))

    def test_returns_false_if_challenge_not_exist(self):
        request = MagicMock(
            data={"proof": {"proofPurpose": "authentication", "challenge": "c44c45c6-e6e1-4db1-ac2d-413aa0eaf438"}}
        )
        self.assertFalse(self.permission.has_permission(request, None))

    @patch("credentials.apps.verifiable_credentials.permissions.didkit_verify_presentation")
    def test_returns_true_if_all_validations_pass(self, mock_didkit_verify_presentation):
        mock_didkit_verify_presentation.return_value = True
        request = MagicMock(
            data={
                "proof": {
                    "proofPurpose": "authentication",
                    "challenge": str(self.issuance_line.uuid),
                }
            }
        )
        self.assertTrue(self.permission.has_permission(request, None))
