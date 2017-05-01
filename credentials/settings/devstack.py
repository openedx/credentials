from credentials.settings._debug_toolbar import *
from credentials.settings.production import *
from credentials.settings.utils import get_logger_config

DEBUG = True
INTERNAL_IPS = ['127.0.0.1']

LOGGING = get_logger_config(debug=True, dev_env=True, local_loglevel='DEBUG')
del LOGGING['handlers']['local']

SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
