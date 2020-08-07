from bok_choy.web_app_test import WebAppTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from acceptance_tests.mixins import CredentialsApiMixin, LoginMixin
from acceptance_tests.pages import LMSDashboardPage, LMSProgramListingPage


class RenderCredentialTests(LoginMixin, WebAppTest, CredentialsApiMixin):

    def setUp(self):
        super().setUp()
        self.create_credential()
        self.change_credential_status('awarded')

    def test_student_dashboard_with_certificate(self):
        """Verify that links to XSeries credentials are displayed on the student dashboard."""
        self.login_with_lms()
        student_dashboard = LMSDashboardPage(self.browser).wait_for_page()
        student_dashboard.is_browser_on_page()

        student_dashboard.go_to_programs_tab()
        program_listing_page = LMSProgramListingPage(self.browser).wait_for_page()
        program_listing_page.is_browser_on_page()

        self.assertTrue(program_listing_page.are_credential_links_present())

        credential_link = program_listing_page.get_credential_link()

        program_listing_page.click_credential_link()
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'action-print-view')))

        # check the credential hash-id matches with rendered credential page.
        self.assertIn(
            self.browser.find_elements_by_css_selector('.accomplishment-stamp-validity span:nth-of-type(2)')[0].text,
            credential_link
        )

    def test_student_dashboard_with_revoked_certificate(self):
        """Verify that no links to XSeries credentials are displayed on the student dashboard if
        status of the credential is revoked."""
        self.change_credential_status('revoked')
        self.login_with_lms()
        student_dashboard = LMSDashboardPage(self.browser).wait_for_page()
        student_dashboard.is_browser_on_page()

        student_dashboard.go_to_programs_tab()
        program_listing_page = LMSProgramListingPage(self.browser).wait_for_page()
        program_listing_page.is_browser_on_page()

        self.assertFalse(program_listing_page.are_credential_links_present())
