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

from credentials.apps.credentials.tests.mixins import OrganizationsDataMixin, ProgramsDataMixin, UserDataMixin
from credentials.apps.credentials.utils import get_organization, get_program, get_user, validate_duplicate_attributes


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
class TestProgramRetrieval(ProgramsDataMixin, TestCase):
    """
    Tests covering the retrieval of programs from the Programs service.
    """
    def setUp(self):
        super(TestProgramRetrieval, self).setUp()
        self.program_id = 1
        cache.clear()

    @httpretty.activate
    def test_get_program(self):
        """
        Verify that the programs data can be retrieved.
        """
        self.mock_programs_api(program_id=self.program_id)

        actual_programs_api_response = get_program(self.program_id)
        self.assertEqual(
            actual_programs_api_response,
            self.PROGRAMS_API_RESPONSE
        )

        # verify the API was actually hit (not the cache)
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @httpretty.activate
    @override_settings(PROGRAMS_CACHE_TTL=1)
    def test_get_program_caching(self):
        """ Verify that when the value is set, the cache is used for getting
        programs.
        """
        self.mock_programs_api(program_id=self.program_id)

        # hit the Programs API twice
        for _ in range(2):
            get_program(self.program_id)

        # verify that only one request has been made
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_program_client_initialization_failure(self, mock_init):
        """ Verify that the function 'get_program' raises exception when API
        client fails to initialize.
        """
        mock_init.side_effect = Exception
        with self.assertRaises(Exception):
            get_program(self.program_id)

    @httpretty.activate
    def test_get_program_data_retrieval_failure(self):
        """ Verify that an empty list will be returned if the data can't be
        retrieved from the Programs API due to a server error.
        """
        self.mock_programs_api_500(program_id=self.program_id)

        with self.assertRaises(exceptions.HttpServerError):
            get_program(self.program_id)

    @httpretty.activate
    def test_get_program_with_no_data(self):
        """ Verify that the function 'get_program' raises exception if the
        Programs API gives 404.
        """
        self.mock_programs_api_404(program_id=self.program_id)

        with self.assertRaises(exceptions.HttpNotFoundError):
            get_program(self.program_id)


@ddt.ddt
class TestOrganizationRetrieval(OrganizationsDataMixin, TestCase):
    """
    Tests for get_organization.
    """
    def setUp(self):
        super(TestOrganizationRetrieval, self).setUp()
        self.organization_key = 'test-org'
        cache.clear()

    @httpretty.activate
    def test_get_organization(self):
        """
        Verify that the organization data can be retrieved.
        """
        self.mock_organizations_api(organization_key=self.organization_key)

        actual_organizations_api_response = get_organization(self.organization_key)
        self.assertEqual(
            actual_organizations_api_response,
            self.ORGANIZATIONS_API_RESPONSE
        )

        # verify the API was actually hit (not the cache)
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @httpretty.activate
    @override_settings(ORGANIZATIONS_CACHE_TTL=1)
    def test_get_organization_caching(self):
        """ Verify that when the value is set, the cache is used for getting
        an organization.
        """
        self.mock_organizations_api(organization_key=self.organization_key)

        # hit the Organizations API twice with the test org
        for _ in range(2):
            get_organization(self.organization_key)

        # verify that only one request has been made
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_organizations_client_initialization_failure(self, mock_init):
        """ Verify that the function 'get_organization' raises exception when API
        client fails to initialize.
        """
        mock_init.side_effect = Exception
        with self.assertRaises(Exception):
            get_organization(self.organization_key)

    @httpretty.activate
    def test_get_organization_data_retrieval_failure(self):
        """ Verify that the data can't be retrieved from Organizations API if
        there is a server error.
        """
        self.mock_organizations_api_500(organization_key=self.organization_key)

        with self.assertRaises(exceptions.HttpServerError):
            get_organization(self.organization_key)

    @httpretty.activate
    def test_get_organization_with_no_data(self):
        """ Verify that the function 'get_organization' raises exception if
        the Organizations API gives 404.
        """
        organization_key = 'invalid-org-key'
        self.mock_organizations_api_404(organization_key)

        with self.assertRaises(exceptions.HttpNotFoundError):
            get_organization(organization_key)


@ddt.ddt
class TestUserRetrieval(UserDataMixin, TestCase):
    """
    Tests for get_user.
    """
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

        actual_user_api_response = get_user(self.username)
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
            get_user(self.username)

        # verify that only one request has been made
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_user_client_initialization_failure(self, mock_init):
        """ Verify that the function 'get_user' raises exception when API
        client fails to initialize.
        """
        mock_init.side_effect = Exception
        with self.assertRaises(Exception):
            get_user(self.username)

    @httpretty.activate
    def test_get_user_data_retrieval_failure(self):
        """ Verify that the data can't be retrieved from User API if there is
        a server error.
        """
        self.mock_user_api_500(username=self.username)

        with self.assertRaises(exceptions.HttpServerError):
            get_user(self.username)

    @httpretty.activate
    def test_get_user_with_no_data(self):
        """ Verify that the function 'get_user' raises exception if the User
        API gives 404.
        """
        username = 'invlaid-username'
        self.mock_user_api_404(username=username)

        with self.assertRaises(exceptions.HttpNotFoundError):
            get_user(username)
