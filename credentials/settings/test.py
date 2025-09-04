import os
from pathlib import Path as path

from edx_django_utils.plugins import add_plugins
from credentials.settings.base import *
from credentials.settings.utils import get_logger_config
from credentials.apps.plugins.constants import PROJECT_TYPE, SettingsType

INSTALLED_APPS += [
    "credentials.apps.edx_credentials_extensions",
]

LOGGING_FORMAT_STRING = os.environ.get("LOGGING_FORMAT_STRING", "")
LOGGING = get_logger_config(debug=False, dev_env=True, local_loglevel="DEBUG", format_string=LOGGING_FORMAT_STRING)
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", ":memory:"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
        "CONN_MAX_AGE": int(os.environ.get("CONN_MAX_AGE", 0)),
    },
}

CACHES = {
    "default": {
        "BACKEND": os.environ.get("CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"),
        "LOCATION": os.environ.get("CACHE_LOCATION", ""),
    }
}

# Local Directories
TEST_ROOT = path("test_root")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_ROOT = str(TEST_ROOT / "uploads")
MEDIA_URL = "/static/uploads/"

SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = "https://test-provider"
BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = "https://test-provider/oauth2"

JWT_AUTH.update(
    {
        "JWT_SECRET_KEY": SOCIAL_AUTH_EDX_OAUTH2_SECRET,
        "JWT_ISSUER": "https://test-provider/oauth2",
        "JWT_AUDIENCE": SOCIAL_AUTH_EDX_OAUTH2_KEY,
    }
)

# Verifiable Credentials
ENABLE_VERIFIABLE_CREDENTIALS = True
VERIFIABLE_CREDENTIALS = {
    "DEFAULT_DATA_MODELS": [
        "credentials.apps.verifiable_credentials.composition.verifiable_credentials.VerifiableCredentialsDataModel",
        "credentials.apps.verifiable_credentials.composition.open_badges.OpenBadgesDataModel",
    ],
    "STATUS_LIST_DATA_MODEL": "credentials.apps.verifiable_credentials.composition.status_list.StatusListDataModel",
    "DEFAULT_ISSUANCE_REQUEST_SERIALIZER": "credentials.apps.verifiable_credentials.issuance.serializers.IssuanceLineSerializer",  # pylint: disable=line-too-long
    "DEFAULT_ISSUER": {
        "ID": "test-issuer-did",
        "KEY": "test-issuer-key",
        "NAME": "test-issuer-name",
    },
    "STATUS_LIST_LENGTH": 10,
    "DEFAULT_STORAGES": [
        "credentials.apps.verifiable_credentials.storages.learner_credential_wallet.LCWallet",
    ],
}

add_plugins(__name__, PROJECT_TYPE, SettingsType.TEST)

# Verifiable Credentials
ENABLE_VERIFIABLE_CREDENTIALS = True
VERIFIABLE_CREDENTIALS = {
    "DEFAULT_ISSUER": {
        "ID": "test-issuer-did",
        "KEY": "test-issuer-key",
        "NAME": "test-issuer-name",
    }
}

LEARNER_RECORD_MFE_RECORDS_PAGE_URL = "http://learner-record-mfe"
add_plugins(__name__, PROJECT_TYPE, SettingsType.TEST)

BADGES_CONFIG["credly"]["USE_SANDBOX"] = True
BADGES_CONFIG["accredible"]["USE_SANDBOX"] = True
BADGES_ENABLED = True
