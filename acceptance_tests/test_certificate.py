from unittest import skipUnless

from bok_choy.web_app_test import WebAppTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from acceptance_tests.config import ENABLE_OAUTH2_TESTS
from acceptance_tests.mixins import LoginMixin


@skipUnless(ENABLE_OAUTH2_TESTS, 'OAuth2 tests are not enabled.')
class RenderCredentialTests(LoginMixin, WebAppTest):

    def test_student_dashboard_with_certificate(self):
        """ Load the credentials from student dashboard."""

        self.login_with_lms()
        link = ".wrapper-xseries-certificates ul li a"
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, link)))

        link_info = self.browser.find_element_by_css_selector(link).get_attribute('href')

        # click is not working so load the credential url in browser.
        self.browser.get(link_info)
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'action-print-view')))
