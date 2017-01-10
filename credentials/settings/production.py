from os import environ

import yaml

from credentials.settings.base import *
from credentials.settings.utils import get_env_setting, get_logger_config


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

LOGGING = get_logger_config()

# AMAZON S3 STORAGE CONFIGURATION
# See: https://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html#settings

# This may be overridden by the yaml in CREDENTIALS_CFG, but it should
# be here as a default.
FILE_STORAGE_BACKEND = {}

CONFIG_FILE = get_env_setting('CREDENTIALS_CFG')
with open(CONFIG_FILE) as f:
    config_from_yaml = yaml.load(f)
    vars().update(config_from_yaml)

    # Load the files storage backend settings for django storages
    vars().update(FILE_STORAGE_BACKEND)

if 'EXTRA_APPS' in locals():
    INSTALLED_APPS += EXTRA_APPS

DB_OVERRIDES = dict(
    PASSWORD=environ.get('DB_MIGRATION_PASS', DATABASES['default']['PASSWORD']),
    ENGINE=environ.get('DB_MIGRATION_ENGINE', DATABASES['default']['ENGINE']),
    USER=environ.get('DB_MIGRATION_USER', DATABASES['default']['USER']),
    NAME=environ.get('DB_MIGRATION_NAME', DATABASES['default']['NAME']),
    HOST=environ.get('DB_MIGRATION_HOST', DATABASES['default']['HOST']),
    PORT=environ.get('DB_MIGRATION_PORT', DATABASES['default']['PORT']),
)

for override, value in DB_OVERRIDES.iteritems():
    DATABASES['default'][override] = value

JWT_AUTH.update({
    'JWT_SECRET_KEY': SOCIAL_AUTH_EDX_OIDC_SECRET,
    'JWT_ISSUER': SOCIAL_AUTH_EDX_OIDC_URL_ROOT,
    'JWT_AUDIENCE': SOCIAL_AUTH_EDX_OIDC_KEY,
})
