from django.core.checks import Error
from django.test import TestCase, override_settings

from ..checks import vc_settings_checks
from ..toggles import ENABLE_VERIFIABLE_CREDENTIALS


class VCSettingsChecksTestCase(TestCase):
    @override_settings(
        VERIFIABLE_CREDENTIALS={
            "DEFAULT_DATA_MODELS": [],
            "DEFAULT_STORAGES": [],
            "DEFAULT_ISSUER": {},
        }
    )
    def test_vc_settings_checks(self):
        errors = vc_settings_checks()
        self.assertEqual(len(errors), 4)

        expected_errors = [
            {
                "id": "verifiable_credentials.E001",
                "msg": "No default data models defined.",
            },
            {
                "id": "verifiable_credentials.E003",
                "msg": "No default storages defined.",
            },
            {
                "id": "verifiable_credentials.E004",
                "msg": f"DEFAULT_ISSUER[ID] is mandatory when {ENABLE_VERIFIABLE_CREDENTIALS.name} is True.",
            },
            {
                "id": "verifiable_credentials.E005",
                "msg": f"DEFAULT_ISSUER[KEY] is mandatory when {ENABLE_VERIFIABLE_CREDENTIALS.name} is True.",
            },
        ]

        for i, error in enumerate(errors):
            with self.subTest(error=error):
                self.assertIsInstance(error, Error)
                self.assertEqual(error.id, expected_errors[i]["id"])
                self.assertEqual(error.msg, expected_errors[i]["msg"])
