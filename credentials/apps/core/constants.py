"""Constants for the core app."""


class Status:
    """Health statuses."""

    OK = "OK"
    UNAVAILABLE = "UNAVAILABLE"


class Role:
    """Named roles (django Groups)."""

    LEARNERS = "Learners"
    ADMINS = "Admins"
