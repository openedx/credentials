import logging
import datetime


from acceptance_tests.config import LMS_EMAIL, LMS_PASSWORD, CREDENTIALS_API_URL, LMS_USERNAME, PROGRAM_ID
from acceptance_tests.pages import LMSLoginPage
from edx_rest_api_client.client import EdxRestApiClient
import jwt

log = logging.getLogger(__name__)


class LoginMixin(object):
    """ Mixin used for log in through LMS login page."""

    def setUp(self):
        super(LoginMixin, self).setUp()
        self.lms_login_page = LMSLoginPage(self.browser)

    def login_with_lms(self):
        """ Visit LMS and login."""
        email = LMS_EMAIL
        password = LMS_PASSWORD

        # Note: We use Selenium directly here (as opposed to bok-choy) to avoid issues with promises being broken.
        self.lms_login_page.browser.get(self.lms_login_page.url())  # pylint: disable=not-callable
        self.lms_login_page.login(email, password)


class CredentialsApiMixin(object):
    def setUp(self):
        super(CredentialsApiMixin, self).setUp()
        self.data = ''

    @property
    def credential_api_client(self):
        now = datetime.datetime.utcnow()
        expires_in = 60
        payload = {
            "iss": 'http://127.0.0.1:8000/oauth2',
            "sub": 1,
            "aud": 'credentials-key',
            "nonce": "dummy-nonce",
            "exp": now + datetime.timedelta(seconds=expires_in),
            "iat": now,
            "preferred_username": 'credentials_service_user',
            "administrator": True,
            "locale": "en",
        }
        try:
            jwt_data = jwt.encode(payload, 'credentials-secret')
            api_client = EdxRestApiClient(CREDENTIALS_API_URL, jwt=jwt_data)
        except Exception:  # pylint: disable=broad-except
            log.exception("Failed to initialize the API client with url '%s'.", CREDENTIALS_API_URL)
            return
        return api_client

    def create_credential(self):
        return self.credential_api_client.user_credentials.post({
            'username': LMS_USERNAME,
            'credential': {'program_id': PROGRAM_ID},
            'attributes': []
        })

    def set_credential_status_awarded(self, data):
        data['status'] = 'awarded'
        self.credential_api_client.user_credentials(data['id']).patch(data)


    def set_credential_status_revoked(self, data):
        data['status'] = 'revoked'
        self.credential_api_client.user_credentials(data['id']).patch(data)

