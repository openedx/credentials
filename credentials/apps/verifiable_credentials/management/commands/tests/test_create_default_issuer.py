import logging
from unittest import mock

from django.test import TestCase, override_settings

from ..create_default_issuer import Command as CreateDefaultIssuerCommand

logger = logging.getLogger(__name__)


class ManagementCommandsTestCase(TestCase):
    @override_settings(ENABLE_VERIFIABLE_CREDENTIALS=False)
    @mock.patch("credentials.apps.verifiable_credentials.management.commands.create_default_issuer.create_issuers")
    def test_handle_when_verifiable_credentials_disabled(self, mock_create_issuers):
        CreateDefaultIssuerCommand().handle()
        mock_create_issuers.assert_not_called()

    @mock.patch("credentials.apps.verifiable_credentials.management.commands.create_default_issuer.create_issuers")
    def test_handle_when_verifiable_credentials_enabled(self, mock_create_issuers):
        CreateDefaultIssuerCommand().handle()
        mock_create_issuers.assert_called_once()
