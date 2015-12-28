""" Accreditor class identifies relative issuer."""
from __future__ import unicode_literals
import logging

from credentials.apps.api import exceptions
from credentials.apps.credentials.issuers import ProgramCertificateIssuer


logger = logging.getLogger(__name__)


class Accreditor(object):
    """ Accreditor class identifies credential type and calls corresponding issuer
    class for generating credential.
    """
    def __init__(self, issuers=None):
        if not issuers:
            issuers = [ProgramCertificateIssuer()]

        self.issuers = issuers
        self._create_credential_type_issuer_map()

    def _create_credential_type_issuer_map(self):
        """Creates a map from credential type slug to a list of credential issuers."""
        self.credential_type_issuer_map = {}
        for issuer in self.issuers:
            slug_value = issuer.issued_credential_type.credential_type_slug
            if slug_value not in self.credential_type_issuer_map:
                self.credential_type_issuer_map[slug_value] = issuer
            else:
                logger.warning("Issuer slug type already exist [%s].", slug_value)

    def issue_credential(self, credential_type, username, **kwargs):
        """Issues a credential.

        Arguments:
            credential_type (string): Type of credential to be issued.
            username (string): Username of the recipient.
            **kwargs: Arbitrary keyword arguments passed to the issuer class.

        Returns:
            UserCredential

        Raises:
            UnsupportedCredentialTypeError: If the specified credential type is not supported (cannot be issued).
        """
        try:
            credential_issuer = self.credential_type_issuer_map[credential_type]
        except KeyError:
            raise exceptions.UnsupportedCredentialTypeError(
                "Credential type [{credential_type}] is not supported.".format(credential_type=credential_type)
            )

        return credential_issuer.issue_credential(username, **kwargs)
