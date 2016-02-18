from unittest import skipUnless

from bok_choy.web_app_test import WebAppTest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from acceptance_tests.config import ENABLE_OAUTH2_TESTS
from acceptance_tests.mixins import LoginMixin
from acceptance_tests.pages import LMSDashboardPage


@skipUnless(ENABLE_OAUTH2_TESTS, 'OAuth2 tests are not enabled.')
class DashboardTests(LoginMixin, WebAppTest):
    def setUp(self):
        """
        Instantiate the page objects.
        """
        super(DashboardTests, self).setUp()
        self.dashboard_page = LMSDashboardPage(self.browser)

    def test_student_dashboard_with_certificate(self):

        self.login_with_lms()
        self.assertTrue(self.browser.find_element_by_css_selector('.title'))
        self.browser.find_element_by_xpath(".//*[@class='wrapper-xseries-certificates']/ul/li/a").click()
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'action-print-view')))
