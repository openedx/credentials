"""
Verifiable Credentials settings testing.
"""


def test_feature_flag_activated(settings):
    assert settings.ENABLE_VERIFIABLE_CREDENTIALS


def test_vc_settings(settings):
    assert settings.VERIFIABLE_CREDENTIALS
