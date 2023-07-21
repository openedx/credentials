from django.test import TestCase

from .. import CredentialDataModel


class CredentialDataModelTestCase(TestCase):
    def test_get_types(self):
        types = CredentialDataModel().get_types()
        self.assertEqual(types, ["VerifiableCredential"])

    def test_resolve_credential_type(self):
        credential_type = CredentialDataModel().resolve_credential_type(None)
        self.assertEqual(credential_type, [])

    def test_collect_hierarchically(self):
        values = CredentialDataModel()._collect_hierarchically("get_types")  # pylint: disable=protected-access
        self.assertEqual(values, ["VerifiableCredential"])

    def test_serialization(self):
        data = {
            "id": "0",
            "name": "Test Name",
            "issuer_id": "456",
            "issuer_name": "Test Issuer",
            "modified": "2022-04-01T12:00:00Z",
            "expiration_date": "2023-04-01T12:00:00Z",
        }
        serialized_data = CredentialDataModel(data).data
        expected_data = {
            "context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3id.org/security/suites/ed25519-2020/v1",
            ],
            "type": ["VerifiableCredential"],
            "issuer": {"id": "456", "name": "Test Issuer", "type": "Profile"},
            "issued": "2022-04-01T12:00:00Z",
            "issuanceDate": "2022-04-01T12:00:00Z",
            "validFrom": "2022-04-01T12:00:00Z",
            "validUntil": "2023-04-01T12:00:00Z",
        }
        self.assertEqual(dict(serialized_data), expected_data)
