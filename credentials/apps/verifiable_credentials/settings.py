"""
Settings for Verifiable Credentials are all namespaced in the VERIFIABLE_CREDENTIALS setting.
This is pretty similar to what the DRF does, like this:

VERIFIABLE_CREDENTIALS = {
    'setting_1': 'value_1',
    'setting_2': 'value_2',
}

This module provides the `vc_setting` object, that is used to access
Verifiable Credentials settings, checking for explicit settings first, then falling
back to the defaults.
"""

import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import setting_changed
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

DEFAULTS = {
    "DEFAULT_DATA_MODELS": [
        "credentials.apps.verifiable_credentials.composition.verifiable_credentials.VerifiableCredentialsDataModel",
        "credentials.apps.verifiable_credentials.composition.open_badges.OpenBadgesDataModel",
    ],
    "DEFAULT_STORAGES": [
        "credentials.apps.verifiable_credentials.storages.learner_credential_wallet.LCWallet",
    ],
    "DEFAULT_ISSUER": {
        "ID": "generate-me-with-didkit-lib",
        "KEY": "generate-me-with-didkit-lib",
        "NAME": "Default (system-wide)",
    },
    "DEFAULT_ISSUANCE_REQUEST_SERIALIZER": "credentials.apps.verifiable_credentials.issuance.serializers.IssuanceLineSerializer",  # pylint: disable=line-too-long
    "DEFAULT_RENDERER": "credentials.apps.verifiable_credentials.issuance.renderers.JSONLDRenderer",
    "STATUS_LIST_STORAGE": "credentials.apps.verifiable_credentials.storages.status_list.StatusList2021",
    "STATUS_LIST_DATA_MODEL": "credentials.apps.verifiable_credentials.composition.status_list.StatusListDataModel",
    "STATUS_LIST_LENGTH": 10000,
}

# List of settings that may be in string import notation:
IMPORT_STRINGS = [
    "DEFAULT_DATA_MODELS",
    "DEFAULT_STORAGES",
    "DEFAULT_ISSUANCE_REQUEST_SERIALIZER",
    "DEFAULT_RENDERER",
    "STATUS_LIST_DATA_MODEL",
    "STATUS_LIST_STORAGE",
]


class VCSettings:
    """
    A settings object that allows Verifiable Credentials settings to be accessed as
    properties. For example:

        from credentials.apps.verifiable_credentials.settings import vc_settings
        print(vc_settings.DEFAULT_STORAGE)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.

    Note:
    This is an internal class that is only compatible with settings namespaced
    under the VERIFIABLE_CREDENTIALS name. It is not intended to be used by 3rd-party
    apps, and test helpers like `override_settings` may not work as expected.
    """

    def __init__(self, explicit_settings=None, defaults=None, import_strings=None):
        if explicit_settings:
            self._explicit_settings = explicit_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def explicit_settings(self):
        if not hasattr(self, "_explicit_settings"):
            self._explicit_settings = getattr(settings, "VERIFIABLE_CREDENTIALS", {})
        return self._explicit_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid VC setting: '%s'" % attr)

        try:
            # Check if present in explicit settings
            val = self.explicit_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_explicit_settings"):
            delattr(self, "_explicit_settings")  # pylint: disable=literal-used-as-attribute


vc_settings = VCSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_vc_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "VERIFIABLE_CREDENTIALS":
        vc_settings.reload()


# Reload on related settings change (testing):
setting_changed.connect(reload_vc_settings)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Improperly configured! Could not import '%s' for VC setting '%s'. %s: %s." % (
            val,
            setting_name,
            e.__class__.__name__,
            e,
        )
        logger.exception(msg)
        raise VerifiableCredentialsImproperlyConfigured(msg)


class VerifiableCredentialsImproperlyConfigured(ImproperlyConfigured):
    """
    Verifiable Credentials settings are somehow improperly configured.
    """
