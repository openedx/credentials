"""Exceptions and error messages used by the credentials API."""


class UnsupportedCredentialTypeError(Exception):
    """ Raised when the Accreditor is asked to issue a type of credential
    for which there is no registered issuer. """


class DuplicateAttributeError(Exception):
    """ Raised when the Accreditor is asked to issue credential with duplicate
    attributes.
    """
