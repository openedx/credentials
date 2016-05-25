import logging

from edx_rest_api_client.client import EdxRestApiClient

from acceptance_tests import config
from acceptance_tests.pages import LMSLoginPage


log = logging.getLogger(__name__)


class LoginMixin(object):
    """ Mixin used for log in through LMS login page."""

    def setUp(self):
        super(LoginMixin, self).setUp()
        self.lms_login_page = LMSLoginPage(self.browser)

    def login_with_lms(self):
        """ Visit LMS and login."""
        email = config.LMS_EMAIL
        password = config.LMS_PASSWORD

        self.lms_login_page.browser.get(self.lms_login_page.url())  # pylint: disable=not-callable
        self.lms_login_page.login(email, password)


class CredentialsApiMixin(object):
    """ Mixin used for login on credentials."""
    def setUp(self):
        super(CredentialsApiMixin, self).setUp()
        self.data = None

    @property
    def credential_api_client(self):
        return EdxRestApiClient(config.CREDENTIALS_API_URL, oauth_access_token=config.ACCESS_TOKEN)


    def create_credential(self):
        """Create user credential for a program."""
        self.data = self.credential_api_client.user_credentials.post({
            'username': config.LMS_USERNAME,
            'credential': {'program_id': config.PROGRAM_ID},
            'attributes': []
        })

    def change_credential_status(self, status):
        """Update the credential status to awarded or revoked."""
        self.data['status'] = status
        self.credential_api_client.user_credentials(self.data['id']).patch(self.data)
