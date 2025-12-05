from os import environ

import yaml

from edx_django_utils.plugins import add_plugins
from credentials.settings.base import *
from credentials.settings.utils import get_env_setting, get_logger_config
from credentials.apps.plugins.constants import PROJECT_TYPE, SettingsType

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ["*"]

# Keep track of the names of settings that represent dicts. Instead of overriding the values in base.py,
# the values read from disk should UPDATE the pre-configured dicts.
DICT_UPDATE_KEYS = ("JWT_AUTH",)

# AMAZON S3 STORAGE CONFIGURATION
# See: https://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html#settings

# This may be overridden by the yaml in CREDENTIALS_CFG, but it should
# be here as a default.
FILE_STORAGE_BACKEND = {}

EMAIL_BACKEND = "django_ses.SESBackend"
AWS_SES_REGION_NAME = environ.get("AWS_SES_REGION_NAME", "us-east-1")
AWS_SES_REGION_ENDPOINT = environ.get("AWS_SES_REGION_ENDPOINT", "email.us-east-1.amazonaws.com")

# Inject plugin settings before the configuration file overrides (so it is possible to manage those settings via environment).
add_plugins(__name__, PROJECT_TYPE, SettingsType.PRODUCTION)

CONFIG_FILE = get_env_setting("CREDENTIALS_CFG")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config_from_yaml = yaml.safe_load(f)

    # Remove the items that should be used to update dicts, and apply them separately rather
    # than pumping them into the local vars.
    dict_updates = {key: config_from_yaml.pop(key, None) for key in DICT_UPDATE_KEYS}

    for key, value in list(dict_updates.items()):
        if value:
            vars()[key].update(value)

    vars().update(config_from_yaml)

    FILE_STORAGE_BACKEND = config_from_yaml.get("FILE_STORAGE_BACKEND", {})

    # Load the files storage backend settings for django storages
    # In django==4.2.24 following line sets AWS variables as per YAML.
    vars().update(FILE_STORAGE_BACKEND)

# make sure this happens after the configuration file overrides so format string can be overridden
LOGGING = get_logger_config(format_string=LOGGING_FORMAT_STRING)

if "EXTRA_APPS" in locals():
    INSTALLED_APPS += EXTRA_APPS

DB_OVERRIDES = dict(
    PASSWORD=environ.get("DB_MIGRATION_PASS", DATABASES["default"]["PASSWORD"]),
    ENGINE=environ.get("DB_MIGRATION_ENGINE", DATABASES["default"]["ENGINE"]),
    USER=environ.get("DB_MIGRATION_USER", DATABASES["default"]["USER"]),
    NAME=environ.get("DB_MIGRATION_NAME", DATABASES["default"]["NAME"]),
    HOST=environ.get("DB_MIGRATION_HOST", DATABASES["default"]["HOST"]),
    PORT=environ.get("DB_MIGRATION_PORT", DATABASES["default"]["PORT"]),
)

for override, value in DB_OVERRIDES.items():
    DATABASES["default"][override] = value
