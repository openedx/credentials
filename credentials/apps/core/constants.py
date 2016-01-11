""" Constants for the core app. """


class Status(object):
    """Health statuses."""
    OK = u"OK"
    UNAVAILABLE = u"UNAVAILABLE"


class Role(object):
    """Named roles (django Groups)."""
    LEARNERS = u"Learners"
    ADMINS = u"Admins"
