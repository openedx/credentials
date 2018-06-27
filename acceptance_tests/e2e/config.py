"""
Configurations for Credential acceptance tests.

"""
import os


def str2bool(s):
    """ Helper method cast str into bool."""
    s = str(s)
    return s.lower() in ('yes', 'true', 't', '1')


# GENERAL CONFIGURATION
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ENABLE_OAUTH2_TESTS = str2bool(os.environ.get('ENABLE_OAUTH2_TESTS', True))

if ACCESS_TOKEN is None:
    raise RuntimeError('A valid OAuth2 access token is required to run acceptance tests.')
# END GENERAL CONFIGURATION


# CREDENTIALS CONFIGURATION
try:
    CREDENTIALS_ROOT_URL = os.environ.get('CREDENTIALS_ROOT_URL').strip('/')
except AttributeError:
    raise RuntimeError('You must provide a valid URL root for the Credentials Service to run acceptance tests.')

CREDENTIALS_API_URL = os.environ.get('CREDENTIALS_API_URL', CREDENTIALS_ROOT_URL + '/api/v2/')
PROGRAM_UUID = os.environ.get('PROGRAM_UUID')

# LMS CONFIGURATION
try:
    LMS_ROOT_URL = os.environ.get('LMS_ROOT_URL').strip('/')
except AttributeError:
    raise RuntimeError('You must provide a valid URL root for the LMS to run acceptance tests.')

LMS_USERNAME = os.environ.get('LMS_USERNAME')
LMS_EMAIL = os.environ.get('LMS_EMAIL')
LMS_PASSWORD = os.environ.get('LMS_PASSWORD')

BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')

if ENABLE_OAUTH2_TESTS and not (LMS_ROOT_URL and LMS_USERNAME and LMS_PASSWORD):
    raise RuntimeError('Configuring LMS settings is required to run OAuth2 tests.')
# END LMS CONFIGURATION
