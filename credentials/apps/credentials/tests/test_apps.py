"""
Tests for credentials configuration.
"""
import ddt
from django.apps import AppConfig
from django.conf import settings
from django.test import TestCase, override_settings
from testfixtures import LogCapture

LOGGER_NAME = 'credentials.apps.credentials.apps'


@ddt.ddt
class CredentialsConfigTests(TestCase):
    """ Tests covering the configuration for programs api, organizations api
    and user api.
    """
    def setUp(self):
        super(CredentialsConfigTests, self).setUp()
        self.app_config = AppConfig.create('credentials.apps.credentials')

    @ddt.data(
        'CREDENTIALS_SERVICE_USER',
        'USER_API_URL',
        'USER_JWT_AUDIENCE',
        'USER_JWT_SECRET_KEY',
    )
    @override_settings()
    def test_credentials_config_settings_failure(self, setting_attribute):
        """ Verify that the exception is raised when there are missing settings
        for the credentials app.
        """
        delattr(settings, setting_attribute)
        expected_error_msg = "The settings {} must be set in order to start the application!".format(setting_attribute)

        with LogCapture(LOGGER_NAME) as log:
            with self.assertRaises(AttributeError):
                self.app_config.ready()

            log.check((LOGGER_NAME, 'CRITICAL', expected_error_msg))
