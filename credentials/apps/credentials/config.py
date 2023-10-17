"""
This module contain configuration settings for the Credentials app.
"""

from edx_toggles.toggles import SettingToggle


# .. toggle_name: SEND_PROGRAM_CERTIFICATE_AWARDED_SIGNAL
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: When True, the system will publish `PROGRAM_CERTIFICATE_AWARDED` signals to the event bus. The
#   `PROGRAM_CERTIFICATE_AWARDED` signal is emit when a certificate has been awarded to a learner and the creation
#   process has completed.
# .. toggle_warning: Will be deprecated in favor of SEND_LEARNING_PROGRAM_CERTIFICATE_LIFECYCLE_EVENTS_TO_BUS
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-08-07
# .. toggle_target_removal_date: TBD
# .. toggle_tickets: https://2u-internal.atlassian.net/browse/APER-2966
SEND_PROGRAM_CERTIFICATE_AWARDED_SIGNAL = SettingToggle(
    "SEND_PROGRAM_CERTIFICATE_AWARDED_SIGNAL", default=False, module_name=__name__
)

# .. toggle_name: SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: When True, the system will publish `PROGRAM_CERTIFICATE_REVOKED` signals to the event bus. The
#   `PROGRAM_CERTIFICATE_REVOKED` signal is emit when the Credentials service has finished updating the learner's
#   UserCredential instance.
# .. toggle_warning: Will be deprecated in favor of SEND_LEARNING_PROGRAM_CERTIFICATE_LIFECYCLE_EVENTS_TO_BUS
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-08-07
# .. toggle_target_removal_date: TBD
# .. toggle_tickets: https://2u-internal.atlassian.net/browse/APER-2966
SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL = SettingToggle(
    "SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL", default=False, module_name=__name__
)
