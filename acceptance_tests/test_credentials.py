from bok_choy.web_app_test import WebAppTest

from acceptance_tests.mixins import LoginMixin
from acceptance_tests.pages import CredentialsExamplePage


class CredentialViewTests(LoginMixin, WebAppTest):

    def test_action_bar_logged_in(self):
        """Verify the certificate action bar appears when logged in."""
        self.login()
        page = CredentialsExamplePage(self.browser)
        page.visit()
        self.assertTrue(page.q(css='.message-actions').is_present())

    def test_action_bar_logged_out(self):
        """Verify the certificate action bar does not appear when logged out."""
        page = CredentialsExamplePage(self.browser)
        page.visit()
        self.assertFalse(page.q(css='.message-actions').is_present())
