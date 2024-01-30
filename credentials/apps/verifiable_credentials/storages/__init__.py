"""
Verifiable Credentials built-in storage backends.
"""

from enum import Enum

from ..settings import vc_settings


class StorageType(Enum):
    MOBILE = "mobile"
    WEB = "web"


class BaseStorage:
    """Base Class for Verifiable Credentials wallets.
    This class provides a blueprint for implementing wallet for Verifiable Credentials.
    """

    ID = None
    NAME = None
    TYPE = None
    DEEP_LINK_URL = None
    ISSUANCE_REQUEST_SERIALIZER = None
    PREFERRED_DATA_MODEL = vc_settings.DEFAULT_DATA_MODELS[0]

    @classmethod
    def get_request_serializer(cls, *args, **kwargs):
        if cls.ISSUANCE_REQUEST_SERIALIZER:
            return cls.ISSUANCE_REQUEST_SERIALIZER(*args, **kwargs)
        return vc_settings.DEFAULT_ISSUANCE_REQUEST_SERIALIZER(*args, **kwargs)

    @classmethod
    def get_data_model(cls, *args, **kwargs):
        return cls.PREFERRED_DATA_MODEL

    @classmethod
    def get_deeplink_url(cls, issuance_line, **kwargs):  # pylint: disable=unused-argument
        return cls.DEEP_LINK_URL

    @classmethod
    def is_mobile(cls):
        return cls.TYPE == StorageType.MOBILE

    @classmethod
    def is_web(cls):
        return cls.TYPE == StorageType.WEB


class MobileWallet(BaseStorage):
    TYPE = StorageType.MOBILE
    APP_LINK_ANDROID = None
    APP_LINK_IOS = None


class WebWallet(BaseStorage):
    TYPE = StorageType.WEB
