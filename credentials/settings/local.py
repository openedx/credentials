from credentials.settings.base import *
from credentials.settings.utils import get_logger_config

DEBUG = True

# Enable offline compression of CSS/JS
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter']

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

# TOOLBAR CONFIGURATION
# See: http://django-debug-toolbar.readthedocs.org/en/latest/installation.html
if os.environ.get('ENABLE_DJANGO_TOOLBAR', False):
    INSTALLED_APPS += (
        'debug_toolbar',
    )

    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

INTERNAL_IPS = ('127.0.0.1',)
# END TOOLBAR CONFIGURATION

# AUTHENTICATION
# Set these to the correct values for your OAuth2/OpenID Connect provider (e.g., devstack)
OAUTH2_PROVIDER_URL = 'http://127.0.0.1:8000/oauth2'
SOCIAL_AUTH_EDX_OIDC_KEY = 'credentials-key'
SOCIAL_AUTH_EDX_OIDC_SECRET = 'credentials-secret'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = OAUTH2_PROVIDER_URL
SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY = SOCIAL_AUTH_EDX_OIDC_SECRET

ENABLE_AUTO_AUTH = True

# PROGRAMS API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
PROGRAMS_CACHE_TTL = 60

# ORGANIZATIONS API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
ORGANIZATIONS_CACHE_TTL = 60

# USER API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
USER_CACHE_TTL = 60

# LOGGING
LOGGING = get_logger_config(debug=DEBUG, dev_env=True, local_loglevel='DEBUG')

#####################################################################
# Lastly, see if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    from .private import *  # pylint: disable=import-error

# do this after private.py, ensuring this section picks up credential overrides.
JWT_AUTH.update({
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SOCIAL_AUTH_EDX_OIDC_SECRET,
    'JWT_ISSUER': OAUTH2_PROVIDER_URL,
    'JWT_AUDIENCE': SOCIAL_AUTH_EDX_OIDC_KEY,
})
