from bok_choy.web_app_test import WebAppTest

from acceptance_tests.mixins import LoginMixin
from acceptance_tests.pages import CredentialsExamplePage


class CredentialViewTests(LoginMixin, WebAppTest):

    def test_action_bar_logged_in(self):
        """Verify the certificate action bar appears when logged in."""
        self.login()
        page = CredentialsExamplePage(self.browser)
        page.visit()
        self.assertNotEqual([], self.browser.find_elements_by_css_selector('.message-actions'))

    def atest_action_bar_logged_out(self):
        """Verify the certificate action bar does not appear when logged out."""
        page = CredentialsExamplePage(self.browser)
        page.visit()
        self.assertEqual([], self.browser.find_elements_by_css_selector('.message-actions'))
