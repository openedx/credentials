import abc

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from acceptance_tests.config import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME, CREDENTIALS_API_URL, LMS_ROOT_URL


class CredentialsDRFPage(PageObject):
    @property
    def url(self):
        return self.page_url

    def __init__(self, browser):
        super().__init__(browser)
        self.page_url = CREDENTIALS_API_URL

    def is_browser_on_page(self):
        return 'Django REST framework' in self.browser.title

    def is_user_logged_in(self):
        # Link with user name should exists now
        return self.q(xpath="//li[@class='dropdown']/a").present

    def login(self):
        # Login by clicking on login button.
        self.q(xpath="//a[contains(text(), 'Log in')]").click()


class LMSPage(PageObject, metaclass=abc.ABCMeta):
    def _build_url(self, path):
        url = f'{LMS_ROOT_URL}/{path}'

        if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
            url = url.replace('://', f'://{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}@')

        return url

    def _is_browser_on_lms_dashboard(self):
        return self.browser.title.startswith('Dashboard')


class LMSLoginPage(LMSPage):
    @property
    def url(self):
        return self._build_url('login')

    def _is_logistration(self):
        return self.q(css='form#login').visible

    def _is_traditional(self):
        return self.q(css='form#login-form').visible

    def is_browser_on_page(self):
        return self._is_logistration() or self._is_traditional()

    def login(self, username, password):
        if self._is_logistration():
            self.q(css='input#login-email').fill(username)
            self.q(css='input#login-password').fill(password)
        else:
            self.q(css='input#email').fill(username)
            self.q(css='input#password').fill(password)

        self.q(css='button.login-button').click()

        # Wait for LMS to redirect to the dashboard
        EmptyPromise(self._is_browser_on_lms_dashboard, 'LMS login redirected to dashboard').fulfill()


class LMSDashboardPage(LMSPage):
    def __init__(self, browser):  # pylint: disable=useless-super-delegation
        super().__init__(browser)

    @property
    def url(self):
        return self._build_url('dashboard')

    def is_browser_on_page(self):
        return self.browser.title.startswith('Dashboard')

    def go_to_programs_tab(self):
        self.q(css='a[href="/dashboard/programs/"]').click()


class LMSProgramListingPage(LMSPage):
    def __init__(self, browser):
        super().__init__(browser)
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
