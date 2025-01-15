"""
Specific for Accredible exceptions.
"""

from credentials.apps.badges.exceptions import BadgesError


class AccredibleError(BadgesError):
    """
    Accredible backend generic error.
    """
