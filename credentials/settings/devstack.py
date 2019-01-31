from credentials.settings._debug_toolbar import *
from credentials.settings.base import *
from credentials.settings.utils import get_logger_config, str2bool

DEBUG = str2bool(os.environ.get('DEBUG', True))

ALLOWED_HOSTS = ['*']

LOGGING = get_logger_config(debug=True, dev_env=True, local_loglevel='DEBUG')
del LOGGING['handlers']['local']

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me')
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'en')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': os.environ.get('CACHE_LOCATION', 'memcached:12211'),
    }
}

CREDENTIALS_SERVICE_USER = os.environ.get('CREDENTIALS_SERVICE_USER', 'credentials_service_user')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'credentials'),
        'USER': os.environ.get('DB_USER', 'credentials001'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', 3306),
        'ATOMIC_REQUESTS': False,
        'CONN_MAX_AGE': 60,
    }
}

INSTALLED_APPS += ['credentials.apps.edx_credentials_extensions']

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/credentials-emails'

DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')
MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')

STATICFILES_STORAGE = os.environ.get('STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')
STATIC_URL = os.environ.get('STATIC_URL', '/static/')

OAUTH2_PROVIDER_URL = 'http://edx.devstack.lms:18000/oauth2'
SOCIAL_AUTH_EDX_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_EDX_OAUTH2_KEY', 'credentials-key')
SOCIAL_AUTH_EDX_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_EDX_OAUTH2_SECRET', 'credentials-secret')
SOCIAL_AUTH_EDX_OAUTH2_ISSUER = os.environ.get('SOCIAL_AUTH_EDX_OAUTH2_ISSUER', 'http://localhost:18000')
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = os.environ.get('SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT', 'http://edx.devstack.lms:18000')
SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL = os.environ.get('SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL', 'http://localhost:18000/logout')
SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT = os.environ.get(
    'SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT', 'http://localhost:18000',
)

CLIENT_CREDENTIALS_EDX_OAUTH2_KEY = os.environ.get('CLIENT_CREDENTIALS_EDX_OAUTH2_KEY', 'client-credentials-key')
CLIENT_CREDENTIALS_EDX_OAUTH2_SECRET = os.environ.get('CLIENT_CREDENTIALS_EDX_OAUTH2_SECRET', 'client-credentials-secret')


SOCIAL_AUTH_REDIRECT_IS_HTTPS = str2bool(os.environ.get('SOCIAL_AUTH_REDIRECT_IS_HTTPS', False))

JWT_AUTH['JWT_ISSUERS'].append({
    'AUDIENCE': 'lms-key',
    'ISSUER': 'http://localhost:18000/oauth2',
    'SECRET_KEY': 'lms-secret',
})
