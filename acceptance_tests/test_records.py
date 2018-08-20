from bok_choy.web_app_test import WebAppTest

from acceptance_tests.mixins import LoginMixin
from acceptance_tests.pages import MyLearnerRecordsPage


# Acceptance tests are heavy-weight, so we do only the bare minimum integration testing here.
# Confirm that the flow across pages is good.
# Make sure we visit each page at least once to get a11y and xss tests going.
class RecordsViewTests(LoginMixin, WebAppTest):

    def setUp(self):
        super().setUp()
        self.login()

    def test_click_to_program_record(self):
        page = MyLearnerRecordsPage(self.browser)
        page.visit()
        page.go_to_record_page()
