import os
from path import Path as path

from credentials.settings.base import *
from credentials.settings.utils import get_logger_config


# TEST SETTINGS
INSTALLED_APPS += (
    'django_nose',
    'credentials.apps.edx_credentials_extensions',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-ignore-docstrings',
    '--logging-level=DEBUG',
]
# LOGGING
LOGGING = get_logger_config(debug=False, dev_env=True, local_loglevel='DEBUG')
# END TEST SETTINGS


# IN-MEMORY TEST DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}
# END IN-MEMORY TEST DATABASE

# Local Directories
TEST_ROOT = path("test_root")
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"

# AUTHENTICATION
OAUTH2_PROVIDER_URL = 'https://test-provider/oauth2'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = OAUTH2_PROVIDER_URL

JWT_AUTH.update({
    'JWT_SECRET_KEY': SOCIAL_AUTH_EDX_OIDC_SECRET,
    'JWT_ISSUER': OAUTH2_PROVIDER_URL,
    'JWT_AUDIENCE': SOCIAL_AUTH_EDX_OIDC_KEY,
})
# END AUTHENTICATION
