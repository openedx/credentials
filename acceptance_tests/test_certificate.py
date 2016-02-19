from unittest import skipUnless

from bok_choy.web_app_test import WebAppTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from acceptance_tests.config import ENABLE_OAUTH2_TESTS
from acceptance_tests.mixins import LoginMixin, CredentialsApiMixin
from acceptance_tests.pages import LMSDashboardPage


@skipUnless(ENABLE_OAUTH2_TESTS, 'OAuth2 tests are not enabled.')
class RenderCredentialTests(LoginMixin, WebAppTest, CredentialsApiMixin):

    def setUp(self):
        super(RenderCredentialTests, self).setUp()
        self.data = self.create_credential()
        self.set_credential_status_awarded(self.data)

    def test_student_dashboard_with_certificate(self):
        """ Load the credentials from student dashboard.
        After successful login user will redirect towards the dashboard page.
        here search the certificate link and load the credential in a browser.
        """
        self.login_with_lms()
        lms = LMSDashboardPage(self.browser).wait_for_page()
        link = ".wrapper-xseries-certificates ul li a"
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, link)))
        self.assertTrue(self.browser.find_element_by_css_selector(".wrapper-xseries-certificates"))
        link_info = self.browser.find_element_by_css_selector(link).get_attribute('href')

        # click is not working so load the credential url in browser.
        self.browser.get(link_info)
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'action-print-view')))

    def test_student_dashboard_without_certificate(self):
        self.set_credential_status_revoked(self.data)
        self.login_with_lms()
        lms = LMSDashboardPage(self.browser).wait_for_page()
        lms.is_browser_on_page()
        self.assertFalse(lms.credential_available())
