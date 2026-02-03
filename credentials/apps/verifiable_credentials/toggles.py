"""
Toggles for verifiable_credentials app.
"""

from edx_toggles.toggles import SettingToggle

# .. toggle_name: ENABLE_VERIFIABLE_CREDENTIALS
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Determines if the Credentials IDA uses digital credentials issuance.
# .. toggle_warning: Requires the Learner Record MFE to be deployed and used in a given environment if toggled to true.
# .. toggle_life_expectancy: permanent
# .. toggle_permanent_justification: Digital Credentials are optional for usage.
# .. toggle_creation_date: 2023-02-02
# .. toggle_use_cases: open_edx
ENABLE_VERIFIABLE_CREDENTIALS = SettingToggle("ENABLE_VERIFIABLE_CREDENTIALS", default=False, module_name=__name__)


def is_verifiable_credentials_enabled():
    return ENABLE_VERIFIABLE_CREDENTIALS.is_enabled()
