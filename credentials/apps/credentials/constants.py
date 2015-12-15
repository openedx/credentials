"""
Credentials API constants.
"""
from __future__ import unicode_literals


class UserCredentialStatus(object):
    """Allowed values for UserCredential.status"""

    AWARDED = "awarded"
    REVOKED = "revoked"


class CertificateType(object):
    """Allowed values for CourseCertificate.certificate_type"""

    HONOR = "honor"
    VERIFIED = "verified"
    PROFESSIONAL = "professional"
