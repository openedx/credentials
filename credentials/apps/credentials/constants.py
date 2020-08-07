"""
Credentials API constants.
"""

# Regex used for UU-IDs.
UUID_REGEX = r'[0-9a-f]{32}'
UUID_PATTERN = fr'(?P<uuid>{UUID_REGEX})'


class UserCredentialStatus:
    """Allowed values for UserCredential.status"""

    AWARDED = 'awarded'
    REVOKED = 'revoked'


class CertificateType:
    """Allowed values for CourseCertificate.certificate_type"""

    HONOR = 'honor'
    VERIFIED = 'verified'
    PROFESSIONAL = 'professional'
    NO_ID_PROFESSIONAL = 'no-id-professional'
