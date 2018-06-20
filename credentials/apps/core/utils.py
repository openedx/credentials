""" Core utils. """


# This function is used by our oauth2 authorization pipeline. See settings/base.py
def update_full_name(strategy, details, user=None, *_args, **_kwargs):
    """Update the user's full name using data from provider."""
    if user:
        full_name = details.get('full_name')

        if full_name and user.full_name != full_name:
            user.full_name = full_name
            strategy.storage.user.changed(user)
