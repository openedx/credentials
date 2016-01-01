"""
Credentials API constants.
"""
from __future__ import unicode_literals

# Regex used for UU-IDs.
UUID_REGEX = r'[0-9a-f]{32}'
UUID_PATTERN = r'(?P<uuid>{})'.format(UUID_REGEX)


class UserCredentialStatus(object):
    """Allowed values for UserCredential.status"""

    AWARDED = "awarded"
    REVOKED = "revoked"


class CertificateType(object):
    """Allowed values for CourseCertificate.certificate_type"""

    HONOR = "honor"
    VERIFIED = "verified"
    PROFESSIONAL = "professional"
