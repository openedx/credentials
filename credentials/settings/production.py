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
AWS_STORAGE_BUCKET_NAME = ''
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

CONFIG_FILE = get_env_setting('CREDENTIALS_CFG')
with open(CONFIG_FILE) as f:
    config_from_yaml = yaml.load(f)
    vars().update(config_from_yaml)

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

if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
