"""
Tests for Issuer class.
"""
import ddt
import httpretty
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from mock import patch
from slumber import exceptions

from credentials.apps.credentials.tests.mixins import UserDataMixin
from credentials.apps.credentials.utils import get_user_data, validate_duplicate_attributes

User = get_user_model()


@ddt.ddt
class ValidateDuplicateAttributesTests(TestCase):
    """ Tests for Validate the attributes method """

    def test_with_non_duplicate_attributes(self):
        """ Verify that the function will return True if no duplicated attributes found."""
        attributes = [
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
            {"name": "grade", "value": "0.85"}
        ]
        self.assertTrue(validate_duplicate_attributes(attributes))

    def test_with_duplicate_attributes(self):
        """ Verify that the function will return False if duplicated attributes found."""

        attributes = [
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
        ]

        self.assertFalse(validate_duplicate_attributes(attributes))


@ddt.ddt
class TestUserRetrieval(UserDataMixin, TestCase):
    """ Tests for get_user_data. """

    def setUp(self):
        super(TestUserRetrieval, self).setUp()
        self.username = 'test-user'
        cache.clear()

    @httpretty.activate
    def test_get_user(self):
        """
        Verify that the user data can be retrieved.
        """
        self.mock_user_api(username=self.username)

        actual_user_api_response = get_user_data(self.username)
        self.assertEqual(
            actual_user_api_response,
            self.USER_API_RESPONSE
        )

        # verify the API was actually hit (not the cache)
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @httpretty.activate
    @override_settings(USER_CACHE_TTL=1)
    def test_get_user_caching(self):
        """ Verify that when the value is set, the cache is used for getting
        a user.
        """
        self.mock_user_api(username=self.username)

        # hit the Organizations API twice with the test org
        for _ in range(2):
            get_user_data(self.username)

        # verify that only one request has been made
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_user_client_initialization_failure(self, mock_init):
        """ Verify that the function 'get_user' raises exception when API
        client fails to initialize.
        """
        mock_init.side_effect = Exception
        with self.assertRaises(Exception):
            get_user_data(self.username)

    @httpretty.activate
    def test_get_user_data_retrieval_failure(self):
        """ Verify that the data can't be retrieved from User API if there is
        a server error.
        """
        self.mock_user_api_500(username=self.username)

        with self.assertRaises(exceptions.HttpServerError):
            get_user_data(self.username)

    @httpretty.activate
    def test_get_user_with_no_data(self):
        """ Verify that the function 'get_user' raises exception if the User
        API gives 404.
        """
        username = 'invlaid-username'
        self.mock_user_api_404(username=username)

        with self.assertRaises(exceptions.HttpNotFoundError):
            get_user_data(username)
