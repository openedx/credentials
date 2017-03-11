from credentials.settings.production import *
from credentials.settings.utils import get_logger_config

DEBUG = True

LOGGING = get_logger_config(debug=True, dev_env=True, local_loglevel='DEBUG')
del LOGGING['handlers']['local']

# TOOLBAR CONFIGURATION
# See: http://django-debug-toolbar.readthedocs.org/en/latest/installation.html
if os.environ.get('ENABLE_DJANGO_TOOLBAR', False):
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

INTERNAL_IPS = ('127.0.0.1',)
# END TOOLBAR CONFIGURATION

SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
