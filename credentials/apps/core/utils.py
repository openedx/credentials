"""Core utils."""


# This function is used by our oauth2 authorization pipeline. See settings/base.py
def update_full_name(strategy, details, user=None, *_args, **_kwargs):  # pylint: disable=keyword-arg-before-vararg
    """Update the user's full name using data from provider."""
    if user:
        full_name = details.get("full_name")

        if full_name and user.full_name != full_name:
            user.full_name = full_name
            strategy.storage.user.changed(user)


def update_lms_user_id(strategy, details, user=None, *_args, **_kwargs):  # pylint: disable=keyword-arg-before-vararg
    if user:
        user_id = details.get("user_id")

        if user_id and user.lms_user_id != user_id:
            user.lms_user_id = user_id
            strategy.storage.user.changed(user)


def _choices(*values):
    """
    Helper for use with model field 'choices'.
    """
    return [(value,) * 2 for value in values]
