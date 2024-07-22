"""
Badges app self-checks.
"""

from django.core.checks import Error, Tags, register

from .utils import credly_check, get_badging_event_types


@register(Tags.compatibility)
def badges_checks(*args, **kwargs):
    """
    Checks the consistency of the badges configurations.

    Raises compatibility Errors upon:
        - BADGES_CONFIG['events'] is empty
        - Credly settings are not properly configured

    Returns:
        List of any Errors.
    """
    errors = []

    if not get_badging_event_types():
        errors.append(
            Error(
                "BADGES_CONFIG['events'] must include at least one event.",
                hint="Add at least one event to BADGES_CONFIG['events'] setting.",
                id="badges.E001",
            )
        )
    if not credly_check():
        errors.append(
            Error(
                "Credly settings are not properly configured.",
                hint="Make sure all required settings are present in BADGES_CONFIG['credly'].",
                id="badges.E002",
            )
        )

    return errors
