from django.apps import AppConfig
from django.conf import settings
from django.test import TestCase
from testfixtures import LogCapture

LOGGER_NAME = "credentials.apps.credentials.apps"


class CredentialsConfigTests(TestCase):
    def test_credentials_config_settings_failure(self):
        """Verify an exception is raised when required settings are missing."""
        app_config = AppConfig.create("credentials.apps.credentials")
        setting_attribute = "CREDENTIALS_SERVICE_USER"
        expected_error_msg = f"The settings {setting_attribute} must be set in order to start the application!"

        delattr(settings, setting_attribute)

        with LogCapture(LOGGER_NAME) as log:
            with self.assertRaises(AttributeError):
                app_config.ready()

            log.check((LOGGER_NAME, "CRITICAL", expected_error_msg))
