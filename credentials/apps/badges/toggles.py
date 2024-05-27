"""
Badges app toggles.
"""

from edx_toggles.toggles import SettingToggle


# .. toggle_name: BADGES_ENABLED
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Determines if the Credentials IDA uses badges functionality.
# .. toggle_life_expectancy: permanent
# .. toggle_permanent_justification: Badges are optional for usage.
# .. toggle_creation_date: 2024-01-12
# .. toggle_use_cases: open_edx
ENABLE_BADGES = SettingToggle("BADGES_ENABLED", default=False, module_name=__name__)


def is_badges_enabled():
    """
    Check main feature flag.
    """

    return ENABLE_BADGES.is_enabled()


def check_badges_enabled(func):
    """
    Decorator for checking the applicability of a badges app.
    """

    def wrapper(*args, **kwargs):
        if is_badges_enabled():
            return func(*args, **kwargs)

    return wrapper
