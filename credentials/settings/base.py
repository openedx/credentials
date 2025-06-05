import os
from datetime import timezone
from os.path import abspath, dirname, join

from corsheaders.defaults import default_headers as corsheaders_default_headers
from django.conf.global_settings import LANGUAGES_BIDI
from edx_toggles.toggles import WaffleSwitch
from edx_django_utils.plugins import get_plugin_apps, add_plugins

from credentials.settings.utils import get_logger_config
from credentials.apps.plugins.constants import PROJECT_TYPE, SettingsType


# PATH vars

here = lambda *x: join(abspath(dirname(__file__)), *x)
PROJECT_ROOT = here("..")
root = lambda *x: join(abspath(PROJECT_ROOT), *x)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("CREDENTIALS_SECRET_KEY", "insecure-secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
# edx-django-sites-extensions will fallback to this site if we cannot identify the site from the hostname.
SITE_ID = 1

# Application definition

# INSTALLED_APPS should always be a list. The EXTRA_APPS setting is used in production to include custom, site-specific,
# apps. That setting is read from YAML as a list.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Database-backed configuration
    "config_models",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "csrf.apps.CsrfAppConfig",  # Enables frontend apps to retrieve CSRF tokens
    "release_util",
    "rest_framework",
    "rest_framework_jwt",
    "social_django",
    "sortedm2m",
    "statici18n",
    "waffle",
    "storages",
    "webpack_loader",
    "django_filters",
    "django_sites_extensions",
    # TODO Set in EXTRA_APPS via configuration
    "edx_credentials_themes",
    "drf_yasg",
    "xss_utils",
    "openedx_events",
]

PROJECT_APPS = [
    "credentials.apps.core",
    "credentials.apps.api",
    "credentials.apps.catalog",
    "credentials.apps.credentials",
    "credentials.apps.edx_django_extensions",
    "credentials.apps.credentials_theme_openedx",
    "credentials.apps.records",
    "credentials.apps.plugins",
    "credentials.apps.verifiable_credentials",
    "credentials.apps.badges",
]

INSTALLED_APPS += THIRD_PARTY_APPS
INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE = (
    "corsheaders.middleware.CorsMiddleware",
    "edx_django_utils.cache.middleware.RequestCacheMiddleware",
    "edx_django_utils.monitoring.DeploymentMonitoringMiddleware",
    "edx_django_utils.monitoring.CookieMonitoringMiddleware",
    "edx_django_utils.monitoring.CachedCustomMonitoringMiddleware",
    "edx_django_utils.monitoring.MonitoringMemoryMiddleware",
    "edx_django_utils.monitoring.FrontendMonitoringMiddleware",
    "edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
    "edx_django_utils.cache.middleware.TieredCacheMiddleware",
    "edx_rest_framework_extensions.middleware.RequestCustomAttributesMiddleware",
    "edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware",
    "crum.CurrentRequestUserMiddleware",
)

# Enable CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = corsheaders_default_headers + ("use-jwt-cookie",)
CORS_ORIGIN_WHITELIST = []

ROOT_URLCONF = "credentials.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "credentials.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# Set this value in the environment-specific files (e.g. local.py, production.py, test.py)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.",
        "NAME": "credentials",
        "USER": "credentials001",
        "PASSWORD": "password",
        "HOST": "localhost",  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        "PORT": "",  # Set to empty string for default.
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": 60,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

# Sourced from edx-platform, which sourced from http://www.localeplanet.com/icu/ and wikipedia
LANGUAGES = [
    ("en", "English"),
    ("rtl", "Right-to-Left Test Language"),
    ("eo", "Dummy Language (Esperanto)"),  # Dummy languaged used for testing
    ("am", "አማርኛ"),  # Amharic
    ("ar", "العربية"),  # Arabic
    ("az", "azərbaycanca"),  # Azerbaijani
    ("bg-bg", "български (България)"),  # Bulgarian (Bulgaria)
    ("bn-bd", "বাংলা (বাংলাদেশ)"),  # Bengali (Bangladesh)
    ("bn-in", "বাংলা (ভারত)"),  # Bengali (India)
    ("bs", "bosanski"),  # Bosnian
    ("ca", "Català"),  # Catalan
    ("ca@valencia", "Català (València)"),  # Catalan (Valencia)
    ("cs", "Čeština"),  # Czech
    ("cy", "Cymraeg"),  # Welsh
    ("da", "dansk"),  # Danish
    ("de-de", "Deutsch (Deutschland)"),  # German (Germany)
    ("el", "Ελληνικά"),  # Greek
    ("en-uk", "English (United Kingdom)"),  # English (United Kingdom)
    ("en@lolcat", "LOLCAT English"),  # LOLCAT English
    ("en@pirate", "Pirate English"),  # Pirate English
    ("es-419", "Español (Latinoamérica)"),  # Spanish (Latin America)
    ("es-ar", "Español (Argentina)"),  # Spanish (Argentina)
    ("es-ec", "Español (Ecuador)"),  # Spanish (Ecuador)
    ("es-es", "Español (España)"),  # Spanish (Spain)
    ("es-mx", "Español (México)"),  # Spanish (Mexico)
    ("es-pe", "Español (Perú)"),  # Spanish (Peru)
    ("et-ee", "Eesti (Eesti)"),  # Estonian (Estonia)
    ("eu-es", "euskara (Espainia)"),  # Basque (Spain)
    ("fa", "فارسی"),  # Persian
    ("fa-ir", "فارسی (ایران)"),  # Persian (Iran)
    ("fi-fi", "Suomi (Suomi)"),  # Finnish (Finland)
    ("fil", "Filipino"),  # Filipino
    ("fr", "Français"),  # French
    ("fr-ca", "Canadien Français"),  # French Canadian
    ("gl", "Galego"),  # Galician
    ("gu", "ગુજરાતી"),  # Gujarati
    ("he", "עברית"),  # Hebrew
    ("hi", "हिन्दी"),  # Hindi
    ("hr", "hrvatski"),  # Croatian
    ("hu", "magyar"),  # Hungarian
    ("hy-am", "Հայերեն (Հայաստան)"),  # Armenian (Armenia)
    ("id", "Bahasa Indonesia"),  # Indonesian
    ("it-it", "Italiano (Italia)"),  # Italian (Italy)
    ("ja-jp", "日本語 (日本)"),  # Japanese (Japan)
    ("kk-kz", "қазақ тілі (Қазақстан)"),  # Kazakh (Kazakhstan)
    ("km-kh", "ភាសាខ្មែរ (កម្ពុជា)"),  # Khmer (Cambodia)
    ("kn", "ಕನ್ನಡ"),  # Kannada
    ("ko-kr", "한국어 (대한민국)"),  # Korean (Korea)
    ("lt-lt", "Lietuvių (Lietuva)"),  # Lithuanian (Lithuania)
    ("ml", "മലയാളം"),  # Malayalam
    ("mn", "Монгол хэл"),  # Mongolian
    ("mr", "मराठी"),  # Marathi
    ("ms", "Bahasa Melayu"),  # Malay
    ("nb", "Norsk bokmål"),  # Norwegian Bokmål
    ("ne", "नेपाली"),  # Nepali
    ("nl-nl", "Nederlands (Nederland)"),  # Dutch (Netherlands)
    ("or", "ଓଡ଼ିଆ"),  # Oriya
    ("pl", "Polski"),  # Polish
    ("pt-br", "Português (Brasil)"),  # Portuguese (Brazil)
    ("pt-pt", "Português (Portugal)"),  # Portuguese (Portugal)
    ("ro", "română"),  # Romanian
    ("ru", "Русский"),  # Russian
    ("si", "සිංහල"),  # Sinhala
    ("sk", "Slovenčina"),  # Slovak
    ("sl", "Slovenščina"),  # Slovenian
    ("sq", "shqip"),  # Albanian
    ("sr", "Српски"),  # Serbian
    ("sv", "svenska"),  # Swedish
    ("sw", "Kiswahili"),  # Swahili
    ("sw-ke", "Kiswahili (Kenya)"),  # Swahili (Kenya)
    ("ta", "தமிழ்"),  # Tamil
    ("te", "తెలుగు"),  # Telugu
    ("th", "ไทย"),  # Thai
    ("tr-tr", "Türkçe (Türkiye)"),  # Turkish (Turkey)
    ("uk", "Українська"),  # Ukranian
    ("ur", "اردو"),  # Urdu
    ("vi", "Tiếng Việt"),  # Vietnamese
    ("uz", "Ўзбек"),  # Uzbek
    ("zh-cn", "中文 (简体)"),  # Chinese (China)
    ("zh-hk", "中文 (香港)"),  # Chinese (Hong Kong)
    ("zh-tw", "中文 (台灣)"),  # Chinese (Taiwan)
]

LANGUAGE_CODE = "en"

LANGUAGES_BIDI = LANGUAGES_BIDI + ["rtl"]

TIME_ZONE = "UTC"
TIME_ZONE_CLASS = timezone.utc


USE_I18N = True

USE_TZ = True

LOCALE_PATHS = (root("conf", "locale"),)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = root("media")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"
# END MEDIA CONFIGURATION


# STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = root("assets")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (root("static"),)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# See: https://django-statici18n.readthedocs.io/en/latest/settings.html
STATICI18N_ROOT = root("static")

WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "bundles/",
        # 'CACHE': True,
        "STATS_FILE": root("..", "webpack-stats.json"),
        "TIMEOUT": 5,
    }
}
# END STATIC FILE CONFIGURATION

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/1.11/ref/settings/#templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": (root("templates"),),
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "credentials.apps.core.context_processors.core",
            ),
            "debug": True,  # Django will only display debug pages if the global DEBUG setting is set to True.
        },
    },
]
CERTIFICATE_LANGUAGES = {}
# END TEMPLATE CONFIGURATION


# COOKIE CONFIGURATION
# The purpose of customizing the cookie names is to avoid conflicts when
# multiple Django services are running behind the same hostname.
# Detailed information at: https://docs.djangoproject.com/en/dev/ref/settings/
SESSION_COOKIE_NAME = "credentials_sessionid"
CSRF_COOKIE_NAME = "credentials_csrftoken"
LANGUAGE_COOKIE_NAME = "credentials_language"
# END COOKIE CONFIGURATION

# AUTHENTICATION CONFIGURATION
LOGIN_URL = "/login/"
LOGOUT_URL = "/logout/"

AUTH_USER_MODEL = "core.User"

AUTHENTICATION_BACKENDS = (
    "auth_backends.backends.EdXOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

ENABLE_AUTO_AUTH = False
AUTO_AUTH_USERNAME_PREFIX = "auto_auth_"

OAUTH_ID_TOKEN_EXPIRATION = 60

SOCIAL_AUTH_STRATEGY = "auth_backends.strategies.EdxDjangoStrategy"

SOCIAL_AUTH_PIPELINE = (
    # This first block is a copy of the default pipelines from auth_backends.strategies.EdxDjangoStrategy.
    # We can't import that module here to reference the default set directly (circular dependencies), so we just
    # duplicate it.
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "auth_backends.pipeline.get_user_if_exists",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "auth_backends.pipeline.update_email",
    # Credentials-specific pipeline below
    "credentials.apps.core.utils.update_full_name",
    "credentials.apps.core.utils.update_lms_user_id",
)

# Set these to the correct values for your OAuth2 provider (e.g., devstack)
SOCIAL_AUTH_EDX_OAUTH2_KEY = "credentials-sso-key"
SOCIAL_AUTH_EDX_OAUTH2_SECRET = "credentials-sso-secret"
SOCIAL_AUTH_EDX_OAUTH2_ISSUER = "http://127.0.0.1:8000"
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = "http://127.0.0.1:8000"
SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL = "http://127.0.0.1:8000/logout"
BACKEND_SERVICE_EDX_OAUTH2_KEY = "credentials-backend-service-key"
BACKEND_SERVICE_EDX_OAUTH2_SECRET = "credentials-backend-service-secret"
BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = "http://127.0.0.1:8000/logout"

# Request the user's permissions in the ID token
EXTRA_SCOPE = ["permissions"]

LOGIN_REDIRECT_URL = "api:v2:credentials-list"
# END AUTHENTICATION CONFIGURATION

# CATALOG API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
PROGRAMS_CACHE_TTL = 60 * 60

# USER API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
USER_CACHE_TTL = 30 * 60

# Credentials service user in Programs service and LMS
CREDENTIALS_SERVICE_USER = "credentials_service_user"

JWT_AUTH = {
    "JWT_ISSUER": [
        {"AUDIENCE": "SET-ME-PLEASE", "ISSUER": "http://127.0.0.1:8000/oauth2", "SECRET_KEY": "SET-ME-PLEASE"}
    ],
    "JWT_ALGORITHM": "HS256",
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_PAYLOAD_GET_USERNAME_HANDLER": lambda d: d.get("preferred_username"),
    "JWT_LEEWAY": 1,
    "JWT_DECODE_HANDLER": "edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler",
    "JWT_PUBLIC_SIGNING_JWK_SET": None,
    "JWT_AUTH_COOKIE": "edx-jwt-cookie",
    "JWT_AUTH_COOKIE_HEADER_PAYLOAD": "edx-jwt-cookie-header-payload",
    "JWT_AUTH_COOKIE_SIGNATURE": "edx-jwt-cookie-signature",
    "JWT_AUTH_HEADER_PREFIX": "JWT",
}

# Email sending
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
ACE_ENABLED_CHANNELS = ["django_email"]
ACE_CHANNEL_DEFAULT_EMAIL = "django_email"
ACE_CHANNEL_TRANSACTIONAL_EMAIL = "django_email"
ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME = ""  # unused, but required to be set or we see an exception

# Set up logging for development use (logging to stdout)
LOGGING_FORMAT_STRING = os.environ.get("LOGGING_FORMAT_STRING", "")
LOGGING = get_logger_config(debug=DEBUG, dev_env=True, local_loglevel="DEBUG", format_string=LOGGING_FORMAT_STRING)

# DRF Settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "credentials.apps.api.authentication.JwtAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.DjangoModelPermissions",),
    "PAGE_SIZE": 20,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "EXCEPTION_HANDLER": "credentials.apps.api.v2.views.credentials_throttle_handler",
}

# Django-ratelimit Settings
RATELIMIT_VIEW = "credentials.apps.records.views.rate_limited"

# DJANGO DEBUG TOOLBAR CONFIGURATION
# http://django-debug-toolbar.readthedocs.org/en/latest/installation.html
if os.environ.get("ENABLE_DJANGO_TOOLBAR", False):
    INSTALLED_APPS += [
        "debug_toolbar",
    ]

    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.history.HistoryPanel",
    ]
# END DJANGO DEBUG TOOLBAR CONFIGURATION

USERNAME_REPLACEMENT_WORKER = "replace with valid username"
LEARNER_STATUS_WORKER = "replace with valid username"

CSRF_COOKIE_SECURE = False
FILE_STORAGE_BACKEND = {}
EXTRA_APPS = []
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
EDX_DRF_EXTENSIONS = {
    "JWT_PAYLOAD_USER_ATTRIBUTE_MAPPING": {
        "administrator": "is_staff",
        "email": "email",
        "full_name": "full_name",
        "user_id": "lms_user_id",
    },
    "ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE": True,
    "OAUTH2_USER_INFO_URL": "http://127.0.0.1:8000/oauth2/user_info",
}
API_ROOT = None
MEDIA_STORAGE_BACKEND = {
    "DEFAULT_FILE_STORAGE": "django.core.files.storage.FileSystemStorage",
    "MEDIA_ROOT": MEDIA_ROOT,
    "MEDIA_URL": MEDIA_URL,
}
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

# .. toggle_name: SEND_EMAIL_ON_PROGRAM_COMPLETION
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: If enabled (and configured), the system will send a congratulatory email to learners upon
#    being awarded a program certificate.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2020-10-08
# .. toggle_target_removal_date: NA
# .. toggle_warning: This is a toggle for the feature
# .. toggle_tickets: MICROBA-521
SEND_EMAIL_ON_PROGRAM_COMPLETION = False
ALLOWED_EMAIL_HTML_TAGS = {
    "a",
    "b",
    "blockquote",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "i",
    "li",
    "ol",
    "p",
    "span",
    "strong",
    "ul",
}

LOGO_TRADEMARK_URL = "https://edx-cdn.org/v3/default/logo-trademark.svg"
LOGO_TRADEMARK_URL_PNG = "https://edx-cdn.org/v3/default/logo-trademark.png"
LOGO_TRADEMARK_URL_SVG = "https://edx-cdn.org/v3/default/logo-trademark.svg"
LOGO_URL = "https://edx-cdn.org/v3/default/logo.svg"
LOGO_URL_PNG = "https://edx-cdn.org/v3/default/logo.png"
LOGO_URL_SVG = "https://edx-cdn.org/v3/default/logo.svg"
LOGO_WHITE_URL = "https://edx-cdn.org/v3/default/logo-white.svg"
LOGO_WHITE_URL_PNG = "https://edx-cdn.org/v3/default/logo-white.png"
LOGO_WHITE_URL_SVG = "https://edx-cdn.org/v3/default/logo-white.svg"
FAVICON_URL = "https://edx-cdn.org/v3/default/favicon.ico"
LOGO_POWERED_BY_OPEN_EDX_URL = "https://edx-cdn.org/v3/prod/open-edx-tag.svg"

# Learner Record MFE Settings
LEARNER_RECORD_MFE_RECORDS_PAGE_URL = ""

# Plugin Django Apps
INSTALLED_APPS.extend(get_plugin_apps(PROJECT_TYPE))
add_plugins(__name__, PROJECT_TYPE, SettingsType.BASE)

# disable indexing on history_date
SIMPLE_HISTORY_DATE_INDEX = False

# Badges settings
BADGES_ENABLED = False
# .. setting_name: BADGES_CONFIG
# .. setting_description: Dictionary with badges settings including enabled badge events, processors, collectors, etc.
BADGES_CONFIG = {
    # # list of the events that should be available in rules configuration interface:
    "events": [
        "org.openedx.learning.course.passing.status.updated.v1",
        "org.openedx.learning.ccx.course.passing.status.updated.v1",
    ],
    "credly": {
        "CREDLY_BASE_URL": "https://credly.com/",
        "CREDLY_API_BASE_URL": "https://api.credly.com/v1/",
        "CREDLY_SANDBOX_BASE_URL": "https://sandbox.credly.com/",
        "CREDLY_SANDBOX_API_BASE_URL": "https://sandbox-api.credly.com/v1/",
        "USE_SANDBOX": False,
    },
    "accredible": {
        "ACCREDIBLE_BASE_URL": "https://dashboard.accredible.com/",
        "ACCREDIBLE_API_BASE_URL": "https://api.accredible.com/v1/",
        "ACCREDIBLE_SANDBOX_BASE_URL": "https://sandbox.dashboard.accredible.com/",
        "ACCREDIBLE_SANDBOX_API_BASE_URL": "https://sandbox.api.accredible.com/v1/",
        "USE_SANDBOX": False,
    },
    "rules": {
        "ignored_keypaths": [
            "user.id",
            "user.is_active",
            "user.pii.username",
            "user.pii.email",
            "user.pii.name",
            "course.display_name",
            "course.start",
            "course.end",
        ],
    },
}

# Event Bus Settings
EVENT_BUS_PRODUCER = "edx_event_bus_redis.create_producer"
EVENT_BUS_CONSUMER = "edx_event_bus_redis.RedisEventConsumer"
EVENT_BUS_REDIS_CONNECTION_URL = "redis://:password@edx.devstack.redis:6379/"
EVENT_BUS_TOPIC_PREFIX = "dev"
# .. setting_name: EVENT_BUS_PRODUCER_CONFIG
# .. setting_default: all events disabled
# .. setting_description: Dictionary of event_types mapped to dictionaries of topic to topic-related configuration.
EVENT_BUS_PRODUCER_CONFIG = {
    # .. setting_name: EVENT_BUS_PRODUCER_CONFIG['org.openedx.learning.badge.awarded.v1']
    #    ['learning-badges-lifecycle']['enabled']
    # .. toggle_implementation: SettingToggle
    # .. toggle_default: True
    # .. toggle_description: Enables sending org.openedx.learning.badge.awarded.v1 events over the event bus.
    # .. toggle_warning: The default may be changed in a later release.
    # .. toggle_use_cases: opt_in
    "org.openedx.learning.badge.awarded.v1": {
        "learning-badges-lifecycle": {"event_key_field": "badge.uuid", "enabled": BADGES_ENABLED},
    },
    # .. setting_name: EVENT_BUS_PRODUCER_CONFIG['org.openedx.learning.badge.revoked.v1']
    #    ['learning-badges-lifecycle']['enabled']
    # .. toggle_implementation: SettingToggle
    # .. toggle_default: True
    # .. toggle_description: Enables sending org.openedx.learning.badge.revoked.v1 events over the event bus.
    # .. toggle_warning: The default may be changed in a later release.
    # .. toggle_use_cases: opt_in
    "org.openedx.learning.badge.revoked.v1": {
        "learning-badges-lifecycle": {"event_key_field": "badge.uuid", "enabled": BADGES_ENABLED},
    },
    # .. setting_name: EVENT_BUS_PRODUCER_CONFIG['org.openedx.learning.program.certificate.awarded.v1']
    #    ['learning-program-certificate-lifecycle']['enabled']
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: False
    # .. toggle_description: Enables sending PROGRAM_CERTIFICATE_AWARDED events over the event bus.
    # .. toggle_warning: The default may be changed in a later release.
    # .. toggle_use_cases: opt_in
    # .. toggle_creation_date: 2023-10-13
    # .. toggle_tickets: https://github.com/openedx/credentials/issues/2241
    "org.openedx.learning.program.certificate.awarded.v1": {
        "learning-program-certificate-lifecycle": {
            "event_key_field": "program_certificate.program.uuid",
            "enabled": False,
        },
    },
    # .. setting_name: EVENT_BUS_PRODUCER_CONFIG['org.openedx.learning.program.certificate.revoked.v1']
    #    ['learning-program-certificate-lifecycle']['enabled']
    # .. toggle_implementation: SettingToggle
    # .. toggle_default: False
    # .. toggle_description: Enables sending PROGRAM_CERTIFICATE_REVOKED events over the event bus.
    # .. toggle_warning: The default may be changed in a later release.
    # .. toggle_use_cases: opt_in
    # .. toggle_creation_date: 2023-10-13
    # .. toggle_tickets: https://github.com/openedx/credentials/issues/2241
    "org.openedx.learning.program.certificate.revoked.v1": {
        "learning-program-certificate-lifecycle": {
            "event_key_field": "program_certificate.program.uuid",
            "enabled": False,
        },
    },
}

# .. toggle_name: LOG_INCOMING_REQUESTS
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Toggle to control whether we log incoming REST requests through the use of the
#   `log_incoming_requests` decorator.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2024-01-25
LOG_INCOMING_REQUESTS = WaffleSwitch("api.log_incoming_requests", module_name=__name__)
