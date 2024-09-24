import logging

from credentials.apps.api import exceptions
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.issuers import CourseCertificateIssuer, ProgramCertificateIssuer


logger = logging.getLogger(__name__)


class Accreditor:
    """Accreditor class identifies credential type and calls corresponding issuer
    class for generating credential.
    """

    def __init__(self, issuers=None):
        self.issuers = issuers or [CourseCertificateIssuer(), ProgramCertificateIssuer()]
        self._create_credential_type_issuer_map()

    def _create_credential_type_issuer_map(self):
        """Creates a map from credential type to a list of credential issuers."""
        self.credential_type_issuer_map = {}
        for issuer in self.issuers:
            credential_type = issuer.issued_credential_type
            registered_issuer = self.credential_type_issuer_map.get(credential_type)

            if registered_issuer:
                logger.warning(
                    "The issuer [%s] is already registered to issue credentials of type [%s]. [%s] will NOT be used.",
                    registered_issuer.__class__,
                    credential_type,
                    issuer.__class__,
                )
            else:
                self.credential_type_issuer_map[credential_type] = issuer

    def issue_credential(
        self,
        credential,
        username,
        status=UserCredentialStatus.AWARDED,
        attributes=None,
        date_override=None,
        request=None,
        lms_user_id=None,
    ):  # pylint: disable=too-many-positional-arguments
        """Issues a credential.

        Arguments:
            credential (AbstractCredential): Type of credential to issue.
            username (str): Username of the recipient.
            status (str): Status of credential.
            attributes (List[dict]): attributes list containing dictionaries of attributes
            request (HttpRequest): request object to build program record absolute uris

        Returns:
            UserCredential

        Raises:
            UnsupportedCredentialTypeError: If the specified credential type is not supported (cannot be issued).
        """
        try:
            credential_issuer = self.credential_type_issuer_map[credential.__class__]
        except KeyError:
            raise exceptions.UnsupportedCredentialTypeError(
                "Unable to issue credential. No issuer is registered for credential type [{}]".format(credential)
            )

        return credential_issuer.issue_credential(
            credential, username, status, attributes, date_override, request, lms_user_id
        )
