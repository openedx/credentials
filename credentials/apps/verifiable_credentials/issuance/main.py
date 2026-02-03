"""
Issuance line processor.
"""

import json
import logging

import didkit
from crum import get_current_request
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from credentials.apps.credentials.constants import UserCredentialStatus

from ..issuance import IssuanceException
from ..issuance.utils import didkit_issue_credential, didkit_verify_credential, get_issuer
from ..settings import vc_settings
from ..storages.utils import get_storage
from .models import IssuanceLine

logger = logging.getLogger(__name__)


class CredentialIssuer:
    """
    Instances of this class manage the whole pipeline of verifiable credential issuance.

    Args:
        data: issuance HTTP API request
        issuance_uuid: (optional) identifier for current issuance line

    Steps:
        - incoming data validation
        - resolving issuance configuration
        - resolving data model to use for verifiable credential composition
        - composed verifiable credential signing
    """

    INACTIVE_STATUSES = [
        UserCredentialStatus.REVOKED,
    ]

    def __init__(self, *, issuance_uuid, data=None):
        self._issuance_line = self._pickup_issuance_line(issuance_uuid)
        self._storage = self._issuance_line.storage
        if data is not None:
            self._validate(data)

    def _pickup_issuance_line(self, issuance_uuid):
        """
        Find previously initiated issuance line for processing.
        """
        issuance_line = IssuanceLine.objects.filter(uuid=issuance_uuid).first()
        if not issuance_line:
            msg = _("Couldn't find such issuance line: [{issuance_uuid}]").format(issuance_uuid=issuance_uuid)
            logger.exception(msg)
            raise ValidationError({"issuance_uuid": msg})

        # double check credential is still active:
        if issuance_line.status in self.INACTIVE_STATUSES:
            msg = _("Seems credential isn't active anymore: [{credential_id}]").format(
                credential_id=issuance_line.user_credential.uuid
            )
            logger.warning(msg)
            raise ValidationError({"reason": msg})

        return issuance_line

    def _validate(self, additional_data):
        """
        Check incoming request data and update issuance line if needed.
        """
        serializer = self._storage.get_request_serializer(self._issuance_line, data=additional_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _render(self, data):
        """
        Shape raw data.
        """
        return vc_settings.DEFAULT_RENDERER().render(data)

    def compose(self):
        """
        Construct an appropriate verifiable credential for signing.
        """
        credential_data = self._issuance_line.construct(context={"request": get_current_request()})
        return self._render(credential_data)

    def sign(self, composed_credential_json):
        """
        Sign the composed digital credential document.

        NOTE:
        -   currently, the Ed25519Signature2020 Linked Data Proof suite is used exclusively (is LC Wallet expected);
        -   future wallets/storages integration may bring another's approaches support;
        """
        err_message = _("Provided data didn't validate")

        didkit_options = {
            "type": "Ed25519Signature2020",
        }
        issuer_key = get_issuer(self._issuance_line.issuer_id).issuer_key

        try:
            verifiable_credential_json = didkit_issue_credential(
                composed_credential_json, json.dumps(didkit_options), issuer_key
            )
        except didkit.DIDKitException as exc:  # pylint: disable=no-member, useless-suppression
            logger.exception(err_message)
            raise IssuanceException(detail=f"{err_message} [{exc}]")
        except ValueError as exc:
            logger.exception(err_message)
            raise IssuanceException(detail=f"{err_message} [{exc}]")

        return verifiable_credential_json

    def verify(self, verifiable_credential_json):
        """
        Check if issued verifiable credentials actually passes verification.

        didkit verification example (JSON): '{"checks":["proof"],"warnings":[],"errors":[]}'
        """
        err_message = _("Issued verifiable credential can't be verified!")

        proof_options = json.dumps({})

        try:
            verification_result = didkit_verify_credential(verifiable_credential_json, proof_options)
            logger.debug("Verifiable credential passed verifiacation: (%s)", verification_result)
        except didkit.DIDKitException as exc:  # pylint: disable=no-member, useless-suppression
            logger.exception(err_message)
            raise IssuanceException(detail=f"{err_message} [{exc}]")

    def issue(self):
        """
        Issue a signed digital credential document by validating, composing, and signing.
        """
        # construction (data collecting and shaping):
        composed_credential = self.compose()

        # signing / structure validation:
        verifiable_credential_json = self.sign(composed_credential)

        # check it's verifiable:
        self.verify(verifiable_credential_json)

        # issuance line finalization:
        self._issuance_line.finalize()

        return json.loads(verifiable_credential_json)

    @classmethod
    def init(cls, *, storage_id, user_credential=None, issuer_id=None):
        """
        The very first action in verifiable credential issuance line.

        NOTE: User credential is not provided for status list special case issuance.
        """
        storage = get_storage(storage_id)
        data_model = storage.get_data_model()

        if issuer_id is None:
            issuer_id = IssuanceLine.resolve_issuer().issuer_id

        issuance_line, __ = IssuanceLine.objects.get_or_create(
            storage_id=storage_id,
            user_credential=user_credential,
            issuer_id=issuer_id,
            processed=not bool(user_credential),
            defaults={
                "data_model_id": data_model.ID,
                "status_index": user_credential and IssuanceLine.get_next_status_index(issuer_id),
                "status": user_credential and user_credential.status,
            },
        )

        return issuance_line
