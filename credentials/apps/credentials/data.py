"""
Public data structures for this app.

This should only ever be consumed and should never import anything other than
stdlib modules, so that it may be consumed everywhere.
"""

from enum import Enum


class UserCredentialStatus(Enum):
    AWARDED = "awarded"
    REVOKED = "revoked"
