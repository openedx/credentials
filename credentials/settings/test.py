import os
from path import Path as path

from credentials.settings.base import *
from credentials.settings.utils import get_logger_config


# TEST SETTINGS
INSTALLED_APPS += (
    'django_nose',
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
JWT_AUTH.update({
    'JWT_SECRET_KEY': 'insecure-secret-key',
    'JWT_ISSUERS': ('test-issuer',),
})
