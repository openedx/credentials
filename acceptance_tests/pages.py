import abc

import six
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from acceptance_tests.config import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME, CREDENTIALS_API_URL, LMS_ROOT_URL


class CredentialsDRFPage(PageObject):  # pylint: disable=abstract-method
    @property
    def url(self):
        return self.page_url

    def __init__(self, browser):
        super(CredentialsDRFPage, self).__init__(browser)
        self.page_url = CREDENTIALS_API_URL

    def is_browser_on_page(self):
        return self.browser.title.startswith('Django REST framework')

    def is_user_logged_in(self):
        # Link with user name should exists now
        return self.q(xpath="//li[@class='dropdown']/a").present

    def login(self):
        # Login by clicking on login button.
        self.q(xpath="//a[contains(text(), 'Log in')]").click()


@six.add_metaclass(abc.ABCMeta)  # pylint: disable=abstract-method
class LMSPage(PageObject):
    def _build_url(self, path):
        url = '{}/{}'.format(LMS_ROOT_URL, path)

        if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
            url = url.replace('://', '://{}:{}@'.format(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD))

        return url

    def _is_browser_on_lms_dashboard(self):
        return self.browser.title.startswith('Dashboard')


class LMSLoginPage(LMSPage):
    def url(self):
        return self._build_url('login')

    def is_browser_on_page(self):
        return self.q(css='form#login').visible

    def login(self, username, password):
        self.q(css='input#login-email').fill(username)
        self.q(css='input#login-password').fill(password)
        self.q(css='button.login-button').click()

        # Wait for LMS to redirect to the dashboard
        EmptyPromise(self._is_browser_on_lms_dashboard, 'LMS login redirected to dashboard').fulfill()


class LMSDashboardPage(LMSPage):
    def __init__(self, browser):
        super(LMSDashboardPage, self).__init__(browser)

    @property
    def url(self):
        return self._build_url('dashboard')

    def is_browser_on_page(self):
        return self.browser.title.startswith('Dashboard')

    def go_to_programs_tab(self):
        self.q(css='a[href^="/dashboard/programs/"]').click()


class LMSProgramListingPage(LMSPage):
    def __init__(self, browser):
        super(LMSProgramListingPage, self).__init__(browser)
        self.credential_css_selector = '.certificate-container'

    @property
    def url(self):
        return self._build_url('dashboard/programs')

    def is_browser_on_page(self):
        return self.browser.title.startswith('Programs')

    def are_credential_links_present(self):
        return self.q(css=self.credential_css_selector).present

    def click_credential_link(self):
        self.q(css=self.credential_css_selector + ' a').click()

    def get_credential_link(self):
        return self.q(css=self.credential_css_selector + ' a').attrs('href')[0]
