"""
Mixins for use during testing.
"""
import json

import httpretty
from django.conf import settings

CONTENT_TYPE = 'application/json'


class UserDataMixin(object):
    """ Mixin mocking User API URLs and providing fake data for testing."""
    USER_API_RESPONSE = {
        "username": "test-user",
        "name": "Test User",
        "email": "test@example.org",
    }

    def mock_user_api(self, username):
        """ Utility for mocking out User API URLs with status code 200."""
        data = self.USER_API_RESPONSE
        self._mock_user_api(username, data)

    def mock_user_api_404(self, username):
        """ Utility for mocking out User API URLs with status code 404."""
        data = None
        self._mock_user_api(username, data, 404)

    def mock_user_api_500(self, username):
        """ Utility for mocking out User API URLs with status code 500."""
        data = None
        self._mock_user_api(username, data, 500)

    def _mock_user_api(self, username, data, status_code=200):
        """ Helper method for mocking out User API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock User API calls.')

        user_api_url = settings.USER_API_URL
        url = '{root}/accounts/{username}'.format(root=user_api_url.strip('/'), username=username)
        body = json.dumps(data)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, url, body=body, content_type=CONTENT_TYPE, status=status_code)
