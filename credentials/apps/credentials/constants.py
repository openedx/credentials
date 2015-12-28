"""
Credentials API constants.
"""
from __future__ import unicode_literals

DRF_DATE_FORMAT = u'%Y-%m-%dT%H:%M:%S.%fZ'


class UserCredentialStatus(object):
    """Allowed values for UserCredential.status"""

    AWARDED = "awarded"
    REVOKED = "revoked"


class CertificateType(object):
    """Allowed values for CourseCertificate.certificate_type"""

    HONOR = "honor"
    VERIFIED = "verified"
    PROFESSIONAL = "professional"
