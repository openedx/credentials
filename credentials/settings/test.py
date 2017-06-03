import os

from path import Path as path

from credentials.settings.base import *
from credentials.settings.utils import get_logger_config


INSTALLED_APPS += [
    'credentials.apps.edx_credentials_extensions',
]

LOGGING = get_logger_config(debug=False, dev_env=True, local_loglevel='DEBUG')
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', ':memory:'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
        'CONN_MAX_AGE': int(os.environ.get('CONN_MAX_AGE', 0)),
    },
}

CACHES = {
    'default': {
        'BACKEND': os.environ.get('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': os.environ.get('CACHE_LOCATION', ''),
    }
}

# Local Directories
TEST_ROOT = path('test_root')
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / 'uploads'
MEDIA_URL = '/static/uploads/'

OAUTH2_PROVIDER_URL = 'https://test-provider/oauth2'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = OAUTH2_PROVIDER_URL

JWT_AUTH.update({
    'JWT_SECRET_KEY': SOCIAL_AUTH_EDX_OIDC_SECRET,
    'JWT_ISSUER': OAUTH2_PROVIDER_URL,
    'JWT_AUDIENCE': SOCIAL_AUTH_EDX_OIDC_KEY,
})
