from django.core.management import call_command
from django.test import TestCase

from credentials.apps.verifiable_credentials.issuance.models import IssuanceConfiguration
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceConfigurationFactory


class RemoveIssuanceConfigurationTestCase(TestCase):
    def setUp(self):
        super().setUp()
        IssuanceConfigurationFactory.create(issuer_id="did:example:123")
        IssuanceConfigurationFactory.create(issuer_id="did:example:456")

    def test_remove_issuer_config(self):
        call_command("remove_issuance_configuration", "did:example:123")
        self.assertFalse(IssuanceConfiguration.objects.filter(issuer_id="did:example:123").exists())
        self.assertTrue(IssuanceConfiguration.objects.filter(issuer_id="did:example:456").exists())
