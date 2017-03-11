# pylint:  disable=missing-docstring
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
        self.issuers = issuers or [ProgramCertificateIssuer()]
        self._create_credential_type_issuer_map()

    def _create_credential_type_issuer_map(self):
        """Creates a map from credential type to a list of credential issuers."""
        self.credential_type_issuer_map = {}
        for issuer in self.issuers:
            credential_type = issuer.issued_credential_type
            registered_issuer = self.credential_type_issuer_map.get(credential_type)

            if not registered_issuer:
                self.credential_type_issuer_map[credential_type] = issuer
            else:
                logger.warning(
                    "The issuer [%s] is already registered to issue credentials of type [%s]. [%s] will NOT be used.",
                    registered_issuer.__class__, credential_type, issuer.__class__)

    def issue_credential(self, credential, username, attributes=None):
        """Issues a credential.

        Arguments:
            credential (AbstractCredential): Type of credential to issue.
            username (string): Username of the recipient.
            attributes (List[dict]): attributes list containing dictionaries of attributes

        Returns:
            UserCredential

        Raises:
            UnsupportedCredentialTypeError: If the specified credential type is not supported (cannot be issued).
        """
        try:
            credential_issuer = self.credential_type_issuer_map[credential.__class__]
        except KeyError:
            raise exceptions.UnsupportedCredentialTypeError(
                "Unable to issue credential. No issuer is registered for credential type [{}]".format(
                    credential
                )
            )

        return credential_issuer.issue_credential(credential, username, attributes)
