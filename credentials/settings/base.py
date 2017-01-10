import os
from os.path import join, abspath, dirname
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
SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles'
)

THIRD_PARTY_APPS = (
    'release_util',
    'rest_framework',
    'rest_framework_swagger',
    'social.apps.django_app.default',
    'waffle',
    'compressor',
    'storages',
)

PROJECT_APPS = (
    'credentials.apps.core',
    'credentials.apps.api',
    'credentials.apps.credentials',
)

INSTALLED_APPS += THIRD_PARTY_APPS
INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
    'waffle.middleware.WaffleMiddleware',
)

ROOT_URLCONF = 'credentials.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'credentials.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
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

LANGUAGE_CODE = 'en-us'

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
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

# Enable offline compression of CSS/JS
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Minify CSS
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
# END STATIC FILE CONFIGURATION

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/1.8/ref/settings/#templates
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

# Set to true if using SSL and running behind a proxy
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',

    # By default python-social-auth will simply create a new user/username if the username
    # from the provider conflicts with an existing username in this system. This custom pipeline function
    # loads existing users instead of creating new ones.
    'auth_backends.pipeline.get_user_if_exists',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'credentials.apps.api.authentication.pipeline_set_user_roles',
)

# Fields passed to the custom user model when creating a new user
SOCIAL_AUTH_USER_FIELDS = ['username', 'email', 'full_name']

# Always raise auth exceptions so that they are properly logged. Otherwise, the PSA middleware will redirect to an
# auth error page and attempt to display the error message to the user (via Django's message framework). We do not
# want the uer to see the message; but, we do want our downstream exception handlers to log the message.
SOCIAL_AUTH_RAISE_EXCEPTIONS = True

# Set these to the correct values for your OAuth2/OpenID Connect provider (e.g., devstack)
SOCIAL_AUTH_EDX_OIDC_KEY = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_SECRET = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL = 'replace-me'
SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY = SOCIAL_AUTH_EDX_OIDC_SECRET

# Request the user's permissions in the ID token
EXTRA_SCOPE = ['permissions']

LOGIN_REDIRECT_URL = '/api/v1/user_credentials/'
# END AUTHENTICATION CONFIGURATION

# CATALOG API CONFIGURATION
# Specified in seconds. Enable caching by setting this to a value greater than 0.
PROGRAMS_CACHE_TTL = 60 * 60

# USER API CONFIGURATION
# Absolute URL used to get user data from the user api in LMS
USER_API_URL = 'http://127.0.0.1:8000/api/user/v1/'
# Specified in seconds. Enable caching by setting this to a value greater than 0.
USER_CACHE_TTL = 30 * 60
USER_JWT_AUDIENCE = 'lms-key'
USER_JWT_SECRET_KEY = 'lms-secret'

# Credentials service user in Programs service and LMS
CREDENTIALS_SERVICE_USER = 'credentials_service_user'

JWT_AUTH = {
    'JWT_SECRET_KEY': None,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_ISSUER': None,
    'JWT_PAYLOAD_GET_USERNAME_HANDLER': lambda d: d.get('preferred_username'),
    'JWT_AUDIENCE': None,
    'JWT_LEEWAY': 1,
    'JWT_DECODE_HANDLER': 'credentials.apps.api.jwt_decode_handler.decode',
}

# Set up logging for development use (logging to stdout)
LOGGING = get_logger_config(debug=DEBUG, dev_env=True, local_loglevel='DEBUG')

# DRF Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'credentials.apps.api.authentication.JwtAuthentication',
        'credentials.apps.api.authentication.BearerAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.DjangoModelPermissions',),
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%SZ'
}

SWAGGER_SETTINGS = {
    'api_version': 'v2',
    'doc_expansion': 'list',
    'is_authenticated': True,
    'permission_denied_handler': 'credentials.apps.api.views.api_docs_permission_denied_handler'
}
