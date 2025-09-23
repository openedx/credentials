from edx_django_utils.plugins import add_plugins
from credentials.settings._debug_toolbar import *
from credentials.settings.base import *
from credentials.apps.plugins.constants import PROJECT_TYPE, SettingsType
from credentials.settings.utils import get_logger_config, str2bool

DEBUG = str2bool(os.environ.get("DEBUG", True))

ALLOWED_HOSTS = ["*"]

LOGGING_FORMAT_STRING = os.environ.get("LOGGING_FORMAT_STRING", "")
LOGGING = get_logger_config(debug=True, dev_env=True, local_loglevel="DEBUG", format_string=LOGGING_FORMAT_STRING)
del LOGGING["handlers"]["local"]

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "en")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": os.environ.get("CACHE_LOCATION", "edx.devstack.memcached:11211"),
        "OPTIONS": {"no_delay": True, "ignore_exc": True, "use_pooling": True},
    }
}

CREDENTIALS_SERVICE_USER = os.environ.get("CREDENTIALS_SERVICE_USER", "credentials_service_user")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "credentials"),
        "USER": os.environ.get("DB_USER", "credentials001"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "password"),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", 3306),
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": 60,
    }
}

INSTALLED_APPS += ["credentials.apps.edx_credentials_extensions"]

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/tmp/credentials-emails"

defaultfile_storage = os.environ.get("DEFAULT_FILE_STORAGE", "django.core.files.storage.FileSystemStorage")

if defaultfile_storage:
    STORAGES["default"]["BACKEND"] = defaultfile_storage

staticfiles_storage = os.environ.get("STATICFILES_STORAGE", "django.contrib.staticfiles.storage.StaticFilesStorage")

if staticfiles_storage:
    STORAGES["staticfiles"]["BACKEND"] = staticfiles_storage

MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")
STATIC_URL = os.environ.get("STATIC_URL", "/static/")

# OAuth2 variables specific to social-auth/SSO login use case.
SOCIAL_AUTH_EDX_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_EDX_OAUTH2_KEY", "credentials-sso-key")
SOCIAL_AUTH_EDX_OAUTH2_SECRET = os.environ.get("SOCIAL_AUTH_EDX_OAUTH2_SECRET", "credentials-sso-secret")
SOCIAL_AUTH_EDX_OAUTH2_ISSUER = os.environ.get("SOCIAL_AUTH_EDX_OAUTH2_ISSUER", "http://localhost:18000")
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = os.environ.get("SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT", "http://edx.devstack.lms:18000")
SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL = os.environ.get("SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL", "http://localhost:18000/logout")
SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT = os.environ.get(
    "SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT",
    "http://localhost:18000",
)

# OAuth2 variables specific to backend service API calls.
BACKEND_SERVICE_EDX_OAUTH2_KEY = os.environ.get("BACKEND_SERVICE_EDX_OAUTH2_KEY", "credentials-backend-service-key")
BACKEND_SERVICE_EDX_OAUTH2_SECRET = os.environ.get(
    "BACKEND_SERVICE_EDX_OAUTH2_SECRET", "credentials-backend-service-secret"
)
BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = os.environ.get(
    "BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL",
    "http://edx.devstack.lms:18000/oauth2",
)

CORS_ORIGIN_WHITELIST = [
    "http://localhost:1990",  # Learner Record MFE
    "http://localhost:18450",  # Subscriptions IDA
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:1990",  # Learner Record MFE
]

SOCIAL_AUTH_REDIRECT_IS_HTTPS = str2bool(os.environ.get("SOCIAL_AUTH_REDIRECT_IS_HTTPS", False))

JWT_AUTH.update(
    {
        "JWT_SECRET_KEY": "lms-secret",
        "JWT_ISSUER": "http://localhost:18000/oauth2",
        "JWT_AUDIENCE": None,
        "JWT_VERIFY_AUDIENCE": False,
        "JWT_PUBLIC_SIGNING_JWK_SET": (
            '{"keys": [{"kid": "devstack_key", "e": "AQAB", "kty": "RSA", "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu'
            "48BUI5VcVtUWIPqzRK_LDSlZYh9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC"
            "4Ee9qG5T38LFe8_oAuFCEntimWxN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzG"
            'y5ZLcTUomo4rZLjghVpq6KZxfS6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw"}]}'
        ),
        "JWT_ISSUERS": [
            {
                "AUDIENCE": "lms-key",
                "ISSUER": "http://localhost:18000/oauth2",
                "SECRET_KEY": "lms-secret",
            }
        ],
    }
)

SEND_EMAIL_ON_PROGRAM_COMPLETION = True

LEARNER_RECORD_MFE_RECORDS_PAGE_URL = "http://localhost:1990/"

add_plugins(__name__, PROJECT_TYPE, SettingsType.DEVSTACK)

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *  # pylint: disable=import-error
except ImportError:
    pass
