# -*- coding: utf-8 -*-
import os
from os.path import abspath, dirname, join

from django.conf.global_settings import LANGUAGES_BIDI

from credentials.settings.utils import get_logger_config

# PATH vars

here = lambda *x: join(abspath(dirname(__file__)), *x)
PROJECT_ROOT = here("..")
root = lambda *x: join(abspath(PROJECT_ROOT), *x)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('CREDENTIALS_SECRET_KEY', 'insecure-secret-key')

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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'release_util',
    'rest_framework',
    'social_django',
    'sortedm2m',
    'statici18n',
    'waffle',
    'storages',
    'webpack_loader',
    'django_filters',
    'django_sites_extensions',
    # TODO Set in EXTRA_APPS via configuration
    'edx_credentials_themes',
    'rest_framework_swagger',
    'hijack',
    'compat',
    'xss_utils'
]

PROJECT_APPS = [
    'credentials.apps.core',
    'credentials.apps.api',
    'credentials.apps.catalog',
    'credentials.apps.credentials',
    'credentials.apps.edx_django_extensions',
    'credentials.apps.credentials_theme_openedx',
    'credentials.apps.records',
]

INSTALLED_APPS += THIRD_PARTY_APPS
INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = (
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'ratelimit.middleware.RatelimitMiddleware',
    'edx_django_utils.cache.middleware.TieredCacheMiddleware',
    'edx_rest_framework_extensions.middleware.RequestMetricsMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',
)

ROOT_URLCONF = 'credentials.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'credentials.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# Set this value in the environment-specific files (e.g. local.py, production.py, test.py)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

# Sourced from edx-platform, which sourced from http://www.localeplanet.com/icu/ and wikipedia
LANGUAGES = [
    ('en', u'English'),
    ('rtl', u'Right-to-Left Test Language'),
    ('eo', u'Dummy Language (Esperanto)'),  # Dummy languaged used for testing
    ('fake2', u'Fake translations'),        # Another dummy language for testing (not pushed to prod)

    ('am', u'አማርኛ'),  # Amharic
    ('ar', u'العربية'),  # Arabic
    ('az', u'azərbaycanca'),  # Azerbaijani
    ('bg-bg', u'български (България)'),  # Bulgarian (Bulgaria)
    ('bn-bd', u'বাংলা (বাংলাদেশ)'),  # Bengali (Bangladesh)
    ('bn-in', u'বাংলা (ভারত)'),  # Bengali (India)
    ('bs', u'bosanski'),  # Bosnian
    ('ca', u'Català'),  # Catalan
    ('ca@valencia', u'Català (València)'),  # Catalan (Valencia)
    ('cs', u'Čeština'),  # Czech
    ('cy', u'Cymraeg'),  # Welsh
    ('da', u'dansk'),  # Danish
    ('de-de', u'Deutsch (Deutschland)'),  # German (Germany)
    ('el', u'Ελληνικά'),  # Greek
    ('en-uk', u'English (United Kingdom)'),  # English (United Kingdom)
    ('en@lolcat', u'LOLCAT English'),  # LOLCAT English
    ('en@pirate', u'Pirate English'),  # Pirate English
    ('es-419', u'Español (Latinoamérica)'),  # Spanish (Latin America)
    ('es-ar', u'Español (Argentina)'),  # Spanish (Argentina)
    ('es-ec', u'Español (Ecuador)'),  # Spanish (Ecuador)
    ('es-es', u'Español (España)'),  # Spanish (Spain)
    ('es-mx', u'Español (México)'),  # Spanish (Mexico)
    ('es-pe', u'Español (Perú)'),  # Spanish (Peru)
    ('et-ee', u'Eesti (Eesti)'),  # Estonian (Estonia)
    ('eu-es', u'euskara (Espainia)'),  # Basque (Spain)
    ('fa', u'فارسی'),  # Persian
    ('fa-ir', u'فارسی (ایران)'),  # Persian (Iran)
    ('fi-fi', u'Suomi (Suomi)'),  # Finnish (Finland)
    ('fil', u'Filipino'),  # Filipino
    ('fr', u'Français'),  # French
    ('fr-ca', u'Canadien Français'),  # French Canadian
    ('gl', u'Galego'),  # Galician
    ('gu', u'ગુજરાતી'),  # Gujarati
    ('he', u'עברית'),  # Hebrew
    ('hi', u'हिन्दी'),  # Hindi
    ('hr', u'hrvatski'),  # Croatian
    ('hu', u'magyar'),  # Hungarian
    ('hy-am', u'Հայերեն (Հայաստան)'),  # Armenian (Armenia)
    ('id', u'Bahasa Indonesia'),  # Indonesian
    ('it-it', u'Italiano (Italia)'),  # Italian (Italy)
    ('ja-jp', u'日本語 (日本)'),  # Japanese (Japan)
    ('kk-kz', u'қазақ тілі (Қазақстан)'),  # Kazakh (Kazakhstan)
    ('km-kh', u'ភាសាខ្មែរ (កម្ពុជា)'),  # Khmer (Cambodia)
    ('kn', u'ಕನ್ನಡ'),  # Kannada
    ('ko-kr', u'한국어 (대한민국)'),  # Korean (Korea)
    ('lt-lt', u'Lietuvių (Lietuva)'),  # Lithuanian (Lithuania)
    ('ml', u'മലയാളം'),  # Malayalam
    ('mn', u'Монгол хэл'),  # Mongolian
    ('mr', u'मराठी'),  # Marathi
    ('ms', u'Bahasa Melayu'),  # Malay
    ('nb', u'Norsk bokmål'),  # Norwegian Bokmål
    ('ne', u'नेपाली'),  # Nepali
    ('nl-nl', u'Nederlands (Nederland)'),  # Dutch (Netherlands)
    ('or', u'ଓଡ଼ିଆ'),  # Oriya
    ('pl', u'Polski'),  # Polish
    ('pt-br', u'Português (Brasil)'),  # Portuguese (Brazil)
    ('pt-pt', u'Português (Portugal)'),  # Portuguese (Portugal)
    ('ro', u'română'),  # Romanian
    ('ru', u'Русский'),  # Russian
    ('si', u'සිංහල'),  # Sinhala
    ('sk', u'Slovenčina'),  # Slovak
    ('sl', u'Slovenščina'),  # Slovenian
    ('sq', u'shqip'),  # Albanian
    ('sr', u'Српски'),  # Serbian
    ('sv', u'svenska'),  # Swedish
    ('sw', u'Kiswahili'),  # Swahili
    ('sw-ke', u'Kiswahili (Kenya)'),  # Swahili (Kenya)
    ('ta', u'தமிழ்'),  # Tamil
    ('te', u'తెలుగు'),  # Telugu
    ('th', u'ไทย'),  # Thai
    ('tr-tr', u'Türkçe (Türkiye)'),  # Turkish (Turkey)
    ('uk', u'Українська'),  # Ukranian
    ('ur', u'اردو'),  # Urdu
    ('vi', u'Tiếng Việt'),  # Vietnamese
    ('uz', u'Ўзбек'),  # Uzbek
    ('zh-cn', u'中文 (简体)'),  # Chinese (China)
    ('zh-hk', u'中文 (香港)'),  # Chinese (Hong Kong)
    ('zh-tw', u'中文 (台灣)'),  # Chinese (Taiwan)
]

LANGUAGE_CODE = 'en'

LANGUAGES_BIDI = LANGUAGES_BIDI + ['rtl']

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = (
    root('conf', 'locale'),
)


# MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = root('media')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
# END MEDIA CONFIGURATION


# STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = root('assets')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    root('static'),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# See: https://django-statici18n.readthedocs.io/en/latest/settings.html
STATICI18N_ROOT = root('static')

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        # 'CACHE': True,
        'STATS_FILE': root('..', 'webpack-stats.json'),
        'TIMEOUT': 5,
    }
}
# END STATIC FILE CONFIGURATION

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/1.11/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': (
            root('templates'),
        ),
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'credentials.apps.core.context_processors.core',
            ),
            'debug': True,  # Django will only display debug pages if the global DEBUG setting is set to True.
        }
    },
]
CERTIFICATE_LANGUAGES = {}
# END TEMPLATE CONFIGURATION


# COOKIE CONFIGURATION
# The purpose of customizing the cookie names is to avoid conflicts when
# multiple Django services are running behind the same hostname.
# Detailed information at: https://docs.djangoproject.com/en/dev/ref/settings/
SESSION_COOKIE_NAME = 'credentials_sessionid'
CSRF_COOKIE_NAME = 'credentials_csrftoken'
LANGUAGE_COOKIE_NAME = 'credentials_language'
# END COOKIE CONFIGURATION

# AUTHENTICATION CONFIGURATION
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'

AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = (
    'auth_backends.backends.EdXOpenIdConnect',
    'django.contrib.auth.backends.ModelBackend',
)

ENABLE_AUTO_AUTH = False
AUTO_AUTH_USERNAME_PREFIX = 'auto_auth_'

OAUTH2_PROVIDER_URL = None
OAUTH_ID_TOKEN_EXPIRATION = 60

SOCIAL_AUTH_STRATEGY = 'auth_backends.strategies.EdxDjangoStrategy'

SOCIAL_AUTH_PIPELINE = (
    # This first block is a copy of the default pipelines from auth_backends.strategies.EdxDjangoStrategy.
    # We can't import that module here to reference the default set directly (circular dependencies), so we just
    # duplicate it.
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'auth_backends.pipeline.get_user_if_exists',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'auth_backends.pipeline.update_email',

    # Credentials-specific pipeline below
    'credentials.apps.core.utils.update_full_name',
)

# Set these to the correct values for your OAuth2/OpenID Connect provider (e.g., devstack)
SOCIAL_AUTH_EDX_OIDC_KEY = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_SECRET = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY = SOCIAL_AUTH_EDX_OIDC_SECRET

# Request the user's permissions in the ID token
EXTRA_SCOPE = ['permissions']

LOGIN_REDIRECT_URL = 'api:v2:credentials-list'
# END AUTHENTICATION CONFIGURATION

# CATALOG API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
PROGRAMS_CACHE_TTL = 60 * 60

# USER API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
USER_CACHE_TTL = 30 * 60

# Credentials service user in Programs service and LMS
CREDENTIALS_SERVICE_USER = 'credentials_service_user'

JWT_AUTH = {
    'JWT_ISSUERS': [],
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_PAYLOAD_GET_USERNAME_HANDLER': lambda d: d.get('preferred_username'),
    'JWT_LEEWAY': 1,
    'JWT_DECODE_HANDLER': 'edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler',
}

# Email sending
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ACE_ENABLED_CHANNELS = ['django_email']
ACE_CHANNEL_DEFAULT_EMAIL = 'django_email'
ACE_CHANNEL_TRANSACTIONAL_EMAIL = 'django_email'
ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME = ''  # unused, but required to be set or we see an exception

# Set up logging for development use (logging to stdout)
LOGGING = get_logger_config(debug=DEBUG, dev_env=True, local_loglevel='DEBUG')

# DRF Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'credentials.apps.api.authentication.JwtAuthentication',
        'credentials.apps.api.authentication.BearerAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.DjangoModelPermissions',),
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%SZ',
    'EXCEPTION_HANDLER': 'credentials.apps.api.v2.views.credentials_throttle_handler',
}

# Django-ratelimit Settings
RATELIMIT_VIEW = 'credentials.apps.records.views.rate_limited'

# django-hijack settings
HIJACK_AUTHORIZE_STAFF = True
HIJACK_URL_ALLOWED_ATTRIBUTES = ('email', 'username',)
# Since we force reload pages when masquerading/hijacking, users don't
# actually hit this page.  The admin endpoint just acts as a safe
# follow through for all users to hit in the django-hijack redirect.
HIJACK_LOGIN_REDIRECT_URL = '/admin/'
HIJACK_AUTHORIZATION_CHECK = 'credentials.apps.records.utils.masquerading_authorized'

# DJANGO DEBUG TOOLBAR CONFIGURATION
# http://django-debug-toolbar.readthedocs.org/en/latest/installation.html
if os.environ.get('ENABLE_DJANGO_TOOLBAR', False):
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
# END DJANGO DEBUG TOOLBAR CONFIGURATION
