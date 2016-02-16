import logging

from acceptance_tests.config import LMS_EMAIL, LMS_PASSWORD
from acceptance_tests.pages import LMSLoginPage


log = logging.getLogger(__name__)


class LoginMixin(object):
    """ Mixin used for log in through LMS login page."""

    def setUp(self):
        super(LoginMixin, self).setUp()
        self.lms_login_page = LMSLoginPage(self.browser)

    def login_with_lms(self):
        """ Visit LMS and login."""
        email = LMS_EMAIL
        password = LMS_PASSWORD

        # Note: We use Selenium directly here (as opposed to bok-choy) to avoid issues with promises being broken.
        self.lms_login_page.browser.get(self.lms_login_page.url())  # pylint: disable=not-callable
        self.lms_login_page.login(email, password)
