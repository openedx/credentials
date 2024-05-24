"""
Specific for Credly exceptions.
"""

from credentials.apps.badges.exceptions import BadgesError


class CredlyError(BadgesError):
    """
    Credly backend generic error.
    """

    pass


class CredlyAPIError(CredlyError):
    """
    Credly API errors.
    """

    pass
