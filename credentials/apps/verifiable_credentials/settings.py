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
