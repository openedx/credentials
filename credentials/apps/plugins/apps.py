"""
Plugins Application Configuration.

Signal handlers are connected here.
"""

from django.apps import AppConfig
from edx_django_utils.plugins import connect_plugin_receivers

from credentials.apps.plugins.constants import PROJECT_TYPE


class PluginsConfig(AppConfig):
    """
    Application Configuration for Plugins.
    """

    name = "credentials.apps.plugins"

    def ready(self):
        """
        Connect plugin receivers to their signals.
        """
        connect_plugin_receivers(PROJECT_TYPE)
