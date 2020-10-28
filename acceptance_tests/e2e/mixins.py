import logging

from edx_rest_api_client.client import EdxRestApiClient

from acceptance_tests import config
from acceptance_tests.pages import LMSLoginPage


log = logging.getLogger(__name__)


class LoginMixin:
    """ Mixin used for log in through LMS login page."""

    def setUp(self):
        super().setUp()
        self.lms_login_page = LMSLoginPage(self.browser)

    def login_with_lms(self):
        """ Visit LMS and login."""
        email = config.LMS_EMAIL
        password = config.LMS_PASSWORD

        self.browser.get(self.lms_login_page.url)  # pylint: disable=not-callable
        self.lms_login_page.login(email, password)


class CredentialsApiMixin:
    """ Mixin used for login on credentials."""
    def setUp(self):
        super().setUp()
        self.data = None

    @property
    def credential_api_client(self):
        try:
            api_client = EdxRestApiClient(config.CREDENTIALS_API_URL, oauth_access_token=config.ACCESS_TOKEN)
        except Exception:  # pylint: disable=broad-except
            log.exception("Failed to initialize the API client with url '%s'.", config.CREDENTIALS_API_URL)
            return
        return api_client

    def create_credential(self):
        """Create user credential for a program."""
        self.data = self.credential_api_client.credentials.post({
            'username': config.LMS_USERNAME,
            'credential': {'program_uuid': config.PROGRAM_UUID},
            'attributes': []
        })

    def change_credential_status(self, status):
        """Update the credential status to awarded or revoked."""
        self.data['status'] = status
        self.credential_api_client.credentials(self.data['uuid']).patch(self.data)
