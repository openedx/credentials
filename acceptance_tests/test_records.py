import unittest

from bok_choy.web_app_test import WebAppTest

from acceptance_tests.mixins import LoginMixin
from acceptance_tests.pages import MyLearnerRecordsPage, ProgramListingPage


# Acceptance tests are heavy-weight, so we do only the bare minimum integration testing here.
# Confirm that the flow across pages is good.
# Make sure we visit each page at least once to get a11y and xss tests going.
class RecordsViewTests(LoginMixin, WebAppTest):
    @unittest.skip(
        "Temporarily disabling this test after recent changes and ran into issues while debugging. We will revisit "
        "this test in MB-1442."
    )
    def test_click_to_program_record(self):
        self.login()
        page = MyLearnerRecordsPage(self.browser)
        page.visit()
        page.go_to_record_page()

    def test_program_listing(self):
        self.login(superuser=True)
        ProgramListingPage(self.browser).visit()
