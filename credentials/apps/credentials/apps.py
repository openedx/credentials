"""
Basic configuration for the credentials app.
"""
import logging

from django.apps import AppConfig
from django.conf import settings


log = logging.getLogger(__name__)


class CredentialsConfig(AppConfig):
    """
    Credentials app configuration.
    """
    name = 'credentials.apps.credentials'
    verbose_name = 'Credentials'

    def ready(self):

        required_config_settings = (
            'CREDENTIALS_SERVICE_USER',
            'PROGRAMS_API_URL', 'PROGRAMS_JWT_AUDIENCE', 'PROGRAMS_JWT_SECRET_KEY',
            'ORGANIZATIONS_API_URL', 'ORGANIZATIONS_AUDIENCE', 'ORGANIZATIONS_SECRET_KEY',
            'USER_API_URL', 'USER_JWT_AUDIENCE', 'USER_JWT_SECRET_KEY',
        )

        missing_config_settings = []
        for setting in required_config_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_config_settings.append(setting)

        if missing_config_settings:
            msg = 'The settings {} must be set in order to start the application!'.format(
                ', '.join(missing_config_settings)
            )
            log.critical(msg)
            raise AttributeError(msg)
