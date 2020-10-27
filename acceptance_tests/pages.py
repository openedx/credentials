import os

from bok_choy.page_object import PageObject, unguarded


CREDENTIALS_ROOT_URL = os.environ.get('CREDENTIALS_ROOT_URL', 'http://localhost:19150').strip('/')


class BasePage(PageObject):  # pylint: disable=abstract-method
    @unguarded
    def wait_for_page(self, *args, **kwargs):  # pylint: disable=arguments-differ
        super().wait_for_page(*args, **kwargs)

        # Bokchoy's wait_for_page call does an accessibility check automatically (if VERIFY_ACCESSIBILITY is on).
        # But Bokchoy only does a xss check (VERIFY_XSS) during the q() method, oddly enough.
        # And its xss checker is an internal function, so we shouldn't just manually call it.
        # Let's force an xss check by calling q() pointlessly here (I'm sure we will end up calling q() naturally
        # anyway, but I'd rather be explicit about this).
        self.q(css='main')

    @unguarded
    def on_url(self):
        return self.browser.current_url == self.url


class CredentialsExamplePage(BasePage):
    url = CREDENTIALS_ROOT_URL + '/credentials/example/'

    def is_browser_on_page(self):
        return self.on_url() and self.q(css='main.accomplishment').is_present()


class MyLearnerRecordsPage(BasePage):
    url = CREDENTIALS_ROOT_URL + '/records/'

    def is_browser_on_page(self):
        return self.on_url() and self.q(css='main.record').is_present()

    def go_to_record_page(self, uuid=None):
        if uuid is None:
            link = self.q(css='a[href^="/records/programs/"').first
            uuid = link.attrs('href')[0].rstrip('/').split('/')[-1]
            link.click()
        else:
            self.q(css=f'a[href="/records/programs/{uuid}/"').first.click()

        next_page = ProgramRecordPage(self.browser, uuid)
        next_page.wait_for_page()
        return next_page


class ProgramRecordPage(BasePage):
    @property
    def url(self):
        return self.page_url

    def __init__(self, browser, uuid, *args, **kwargs):
        super().__init__(browser, *args, **kwargs)
        self.page_url = CREDENTIALS_ROOT_URL + f'/records/programs/{uuid}/'

    def is_browser_on_page(self):
        return self.on_url() and self.q(css='main.program-record-wrapper').is_present()


class ProgramListingPage(BasePage):
    url = CREDENTIALS_ROOT_URL + '/program-listing/'

    def is_browser_on_page(self):
        return self.on_url() and self.q(css='main.record').is_present()
