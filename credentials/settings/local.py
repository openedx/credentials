from credentials.settings._debug_toolbar import *  # Enables toolbar
from credentials.settings.base import *
from credentials.settings.utils import get_logger_config

DEBUG = True
INTERNAL_IPS = ['127.0.0.1']
ALLOWED_HOSTS = ['*']

# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# END CACHE CONFIGURATION

# DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': root('default.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}
# END DATABASE CONFIGURATION

# EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# END EMAIL CONFIGURATION

# AUTHENTICATION
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

# Set these to the correct values for your OAuth2 provider (e.g., devstack)
OAUTH2_PROVIDER_URL = 'http://localhost:18000/oauth2'
SOCIAL_AUTH_EDX_OAUTH2_KEY = 'credentials-key'
SOCIAL_AUTH_EDX_OAUTH2_SECRET = 'credentials-secret'
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = OAUTH2_PROVIDER_URL

CLIENT_CREDENTIALS_EDX_OAUTH2_KEY = 'client-credentials-key'
CLIENT_CREDENTIALS_EDX_OAUTH2_SECRET = 'client-credentials-secret'

ENABLE_AUTO_AUTH = True

# CATALOG API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
PROGRAMS_CACHE_TTL = 60

# USER API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
USER_CACHE_TTL = 60

# LOGGING
LOGGING = get_logger_config(debug=True, dev_env=True, local_loglevel='DEBUG')

#####################################################################
# Lastly, see if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    from .private import *  # pylint: disable=import-error

# do this after private.py, ensuring this section picks up credential overrides.
JWT_AUTH.update({
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SOCIAL_AUTH_EDX_OAUTH2_SECRET,
    'JWT_ISSUER': OAUTH2_PROVIDER_URL,
    'JWT_AUDIENCE': SOCIAL_AUTH_EDX_OAUTH2_KEY,
})
