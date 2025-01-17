from urllib.parse import urlencode, urljoin

from crum import get_current_request
from django.urls import reverse
from django.utils.translation import gettext as _

from ..composition.open_badges import OpenBadgesDataModel
from ..issuance.models import IssuanceLine
from ..issuance.serializers import IssuanceLineSerializer
from ..storages import MobileWallet


class LCWalletRequest(IssuanceLineSerializer):
    """
    Specific storage adapter.
    Another storage may not provide expected shape for issuance request (field names, structure).
    """

    class Meta:
        model = IssuanceLine
        fields = [
            "subject_id",
        ]

    def to_internal_value(self, data):
        """
        Maps storage-specific request properties to the unified verifiable credential source data.
        """
        self.swap_value(data, "holder", "subject_id")
        return super().to_internal_value(data)


class LCWallet(MobileWallet):
    """
    Learner Credential Wallet by DCC.
    """

    ID = "lc_wallet"
    NAME = _("Learner Credential Wallet")

    APP_LINK_ANDROID = "https://play.google.com/store/apps/details?id=app.lcw"
    APP_LINK_IOS = "https://apps.apple.com/app/learner-credential-wallet/id1590615710"
    DEEP_LINK_URL = "dccrequest://request"

    PREFERRED_DATA_MODEL = OpenBadgesDataModel
    ISSUANCE_REQUEST_SERIALIZER = LCWalletRequest

    @classmethod
    def get_deeplink_url(cls, issuance_line, **kwargs):
        request = get_current_request()
        if not request:
            return None

        issuance_base_url = request.build_absolute_uri().split(request.path)[0]

        params = {
            "issuer": issuance_line.issuer_id,
            "vc_request_url": urljoin(
                issuance_base_url,
                reverse(
                    "verifiable_credentials:api:v1:credentials-issue",
                    kwargs={"issuance_line_uuid": issuance_line.uuid},
                ),
            ),
            "auth_type": "bearer",
            "challenge": issuance_line.uuid,
            "vp_version": "1.1",
        }
        return f"{cls.DEEP_LINK_URL}?{urlencode(params)}"
