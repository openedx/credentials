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

    name = "credentials.apps.credentials"
    verbose_name = "Credentials"

    def ready(self):
        # connect signal handlers for event bus functionality
        from credentials.apps.credentials import signals  # pylint: disable=unused-import,import-outside-toplevel

        required_config_settings = ("CREDENTIALS_SERVICE_USER",)

        missing_config_settings = []
        for setting in required_config_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_config_settings.append(setting)

        if missing_config_settings:
            msg = "The settings {} must be set in order to start the application!".format(
                ", ".join(missing_config_settings)
            )
            log.critical(msg)
            raise AttributeError(msg)
