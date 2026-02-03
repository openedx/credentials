"""
Status List issuance utils.

Status list is managed for each Issuer separately.
Status lists are verifiable credentials themselves, but with a specific shape.
"""

import logging

from django.utils.translation import gettext as _

from ..issuance.main import CredentialIssuer
from ..settings import vc_settings
from . import IssuanceException

logger = logging.getLogger(__name__)


def issue_status_list(issuer_id):
    """
    Initiate Status List 2021 for Issuer.

    NOTE: "Status List 2021" is a special kind of a verifiable credential.
    """
    issuance_line = CredentialIssuer.init(storage_id=vc_settings.STATUS_LIST_STORAGE.ID, issuer_id=issuer_id)
    credential_issuer = CredentialIssuer(issuance_uuid=issuance_line.uuid)

    try:
        return credential_issuer.issue()
    except IssuanceException:
        msg = _("Status List generation failed: [{issuer_id}]").format(issuer_id=issuance_line.issuer_id)
        logger.exception(msg)

    return None
