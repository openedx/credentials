"""
Verifiable Credentials self-checks.
"""

from django.core.checks import Error, Tags, register

from .settings import vc_settings
from .toggles import ENABLE_VERIFIABLE_CREDENTIALS


@register(Tags.compatibility)
def vc_settings_checks(*args, **kwargs):
    """
    Checks the consistency of the verifiable_credentials settings.

    Raises compatibility Errors upon:
        - No default data models defined
        - No default storages defined
        - DEFAULT_ISSUER[ID] is not set
        - DEFAULT_ISSUER[KEY] is not set

    Returns:
        List of any Errors.
    """
    errors = []

    if not vc_settings.DEFAULT_DATA_MODELS:
        errors.append(
            Error(
                "No default data models defined.",
                hint="Add at least one data model to the DEFAULT_DATA_MODELS setting.",
                id="verifiable_credentials.E001",
            )
        )

    if not vc_settings.DEFAULT_STORAGES:
        errors.append(
            Error(
                "No default storages defined.",
                hint="Add at least one storage to the DEFAULT_STORAGES setting.",
                id="verifiable_credentials.E003",
            )
        )

    if not vc_settings.DEFAULT_ISSUER.get("ID"):
        errors.append(
            Error(
                f"DEFAULT_ISSUER[ID] is mandatory when {ENABLE_VERIFIABLE_CREDENTIALS.name} is True.",
                hint=" Set DEFAULT_ISSUER[ID] to a valid DID string.",
                id="verifiable_credentials.E004",
            )
        )

    if not vc_settings.DEFAULT_ISSUER.get("KEY"):
        errors.append(
            Error(
                f"DEFAULT_ISSUER[KEY] is mandatory when {ENABLE_VERIFIABLE_CREDENTIALS.name} is True.",
                hint="Set DEFAULT_ISSUER[KEY] to a valid key string.",
                id="verifiable_credentials.E005",
            )
        )

    return errors
