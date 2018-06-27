import os

from bok_choy.page_object import PageObject, unguarded

CREDENTIALS_ROOT_URL = os.environ.get('CREDENTIALS_ROOT_URL', 'http://localhost:19150').strip('/')


class BasePage(PageObject):  # pylint: disable=abstract-method
    react_selector = None

    @unguarded
    def visit(self):
        super().visit()
        if self.react_selector:
            self.wait_for_element_presence(self.react_selector, 'React is loaded')
        self.a11y_audit.check_for_accessibility_errors()


class CredentialsExamplePage(BasePage):
    url = CREDENTIALS_ROOT_URL + '/credentials/example/'

    def is_browser_on_page(self):
        return self.browser.title.startswith('Professional Certificate | ')
