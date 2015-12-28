"""Exceptions and error messages used by the credentials API."""
from __future__ import unicode_literals


class UnsupportedCredentialTypeError(Exception):
    """ Raised when the Accreditor is asked to issue a type of credential
    for which there is no registered issuer. """
    pass


class InvalidCredentialIdError(Exception):
    """ Raised when the credential id is invalid. """
    pass
