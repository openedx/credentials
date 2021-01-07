class MissingCertificateLogoError(Exception):
    """Raised when a Program fetched as part of a program certificate configuration
    has an organization without a defined certificate logo image url
    """


class NoMatchingProgramException(Exception):
    """
    Raised when a ProgramCertificate doesn't have a matching program linked to it.
    """
