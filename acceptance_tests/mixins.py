import logging
import uuid

import requests

from acceptance_tests.config import (
    LMS_AUTO_AUTH,
    CREDENTIALS_ROOT_URL,
    LMS_PASSWORD,
    LMS_EMAIL,
    LMS_ROOT_URL,
    BASIC_AUTH_USERNAME,
    BASIC_AUTH_PASSWORD,
    CREDENTIALS_API_URL,
    LMS_USERNAME,
    CREDENTIALS_API_TOKEN,
    MAX_COMPLETION_RETRIES,
)
from acceptance_tests.pages import LMSLoginPage, LMSDashboardPage, LMSRegistrationPage

log = logging.getLogger(__name__)


class LmsUserMixin(object):
    password = 'edx'

    def get_lms_user(self):
        if LMS_AUTO_AUTH:
            return self.create_lms_user()

        return LMS_USERNAME, LMS_PASSWORD, LMS_EMAIL

    def generate_user_credentials(self, username_prefix):
        username = username_prefix + uuid.uuid4().hex[0:10]
        password = self.password
        email = '{}@example.com'.format(username)
        return username, email, password

    def create_lms_user(self):
        username, email, password = self.generate_user_credentials(username_prefix='auto_auth_')

        url = '{host}/auto_auth?no_login=true&username={username}&password={password}&email={email}'.format(
            host=LMS_ROOT_URL,
            username=username,
            password=password,
            email=email
        )
        auth = None

        if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
            auth = (BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD)

        requests.get(url, auth=auth)

        return username, password, email


class LogistrationMixin(LmsUserMixin):
    def setUp(self):
        super(LogistrationMixin, self).setUp()
        self.lms_login_page = LMSLoginPage(self.browser)
        self.lms_registration_page = LMSRegistrationPage(self.browser)

    def login(self):
        self.login_with_lms()

    def login_with_lms(self, email=None, password=None):
        """ Visit LMS and login. """
        email = email or LMS_EMAIL
        password = password or LMS_PASSWORD

        # Note: We use Selenium directly here (as opposed to bok-choy) to avoid issues with promises being broken.
        self.lms_login_page.browser.get(self.lms_login_page.url())
        self.lms_login_page.login(email, password)


class LogoutMixin(object):
    def logout(self):
        url = '{}/accounts/logout/'.format(CREDENTIALS_ROOT_URL)
        self.browser.get(url)


