""" Constants for the core app. """


class Status(object):
    """Health statuses."""
    OK = 'OK'
    UNAVAILABLE = 'UNAVAILABLE'


class Role(object):
    """Named roles (django Groups)."""
    ADMINS = 'Admins'
