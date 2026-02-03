"""
Constants used by django app plugins
"""

# expose constants from edx-django-utils so plugins using these continue to work
from edx_django_utils.plugins import PluginContexts  # pylint: disable=unused-import
from edx_django_utils.plugins import PluginSettings  # pylint: disable=unused-import
from edx_django_utils.plugins import PluginSignals  # pylint: disable=unused-import
from edx_django_utils.plugins import PluginURLs  # pylint: disable=unused-import

PROJECT_TYPE = "credentials.djangoapp"


class SettingsType:
    """
    The SettingsType enum defines the possible values for the settings files
    that are available for extension in the edx-platform. Plugin apps use these
    values to declare explicitly which setting (in the specified project) they are extending.
    """

    PRODUCTION = "production"
    BASE = "base"
    DEVSTACK = "devstack"
    TEST = "test"
