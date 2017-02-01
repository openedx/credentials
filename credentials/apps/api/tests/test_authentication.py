"""
Tests for REST API Authentication
"""

import ddt
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from credentials.apps.api.authentication import BearerAuthentication, JwtAuthentication, pipeline_set_user_roles
from credentials.apps.api.tests.mixins import JwtMixin
from credentials.apps.core.constants import Role
from credentials.apps.core.tests.factories import UserFactory


@ddt.ddt
class TestJWTAuthentication(JwtMixin, TestCase):
    """
    Test id_token authentication used with the browseable API.
    """
    USERNAME = 'test-username'

    def test_no_preferred_username(self):
        """
        Ensure the service gracefully handles an inability to extract a username from the id token.
        """
        # with preferred_username: all good
        authentication = JwtAuthentication()
        user = authentication.authenticate_credentials({'preferred_username': self.USERNAME})
        self.assertEqual(user.username, self.USERNAME)

        # missing preferred_username: exception
        authentication = JwtAuthentication()
        with self.assertRaises(AuthenticationFailed):
            authentication.authenticate_credentials({})

    def test_admin_user(self):
        """
        Ensure the service gracefully handles an admin role from the id token.
        """
        authentication = JwtAuthentication()
        user = authentication.authenticate_credentials(
            {
                'preferred_username': self.USERNAME,
                'administrator': True
            }
        )
        self.assertEqual(user.username, self.USERNAME)
        self.assertEqual(len(user.groups.all()), 1)
        self.assertEqual(user.groups.all()[0].name, Role.ADMINS)

    @ddt.data('exp', 'iat')
    def test_required_claims(self, claim):
        """
        Verify that tokens that do not carry 'exp' or 'iat' claims are rejected
        """
        authentication = JwtAuthentication()
        user = UserFactory()
        jwt_payload = self.default_payload(user)
        del jwt_payload[claim]
        jwt_value = self.generate_token(jwt_payload)
        request = APIRequestFactory().get('dummy', HTTP_AUTHORIZATION='JWT {}'.format(jwt_value))
        with self.assertRaises(AuthenticationFailed):
            authentication.authenticate(request)


@ddt.ddt
class TestPipelineUserRoles(TestCase):
    """
    Ensure that user roles are set correctly based on a payload containing claims
    about the user, during login via social auth.
    """

    def setUp(self):
        self.user = UserFactory.create()
        super(TestPipelineUserRoles, self).setUp()

    def assert_has_admin_role(self, has_role=True):
        """
        Shorthand convenience.
        """
        _assert = self.assertTrue if has_role else self.assertFalse
        _assert(self.user.groups.filter(name=Role.ADMINS).exists())

    def assert_pipeline_result(self, result):
        """
        Shorthand convenience.  Ensures that the output of the pipeline function
        adheres to the social auth pipeline interface and won't break the auth flow.
        """
        self.assertEqual(result, {'user': self.user})

    def test_admin_role_is_assigned(self):
        """
        Make sure the user is assigned the ADMINS role if the "administrator" claim
        is set to true.
        """
        self.assert_has_admin_role(False)
        result = pipeline_set_user_roles({"administrator": True}, self.user)
        self.assert_has_admin_role()
        self.assert_pipeline_result(result)

    @ddt.data({"administrator": False}, {})
    def test_admin_role_is_unassigned(self, payload):
        """
        Make sure the user is unassigned from the ADMINS role, even if they previously
        had that role, if the "administrator" claim is not set to true.
        """
        self.user.groups.add(Group.objects.get(name=Role.ADMINS))  # pylint: disable=no-member
        self.assert_has_admin_role()
        result = pipeline_set_user_roles(payload, self.user)
        self.assert_has_admin_role(False)
        self.assert_pipeline_result(result)

    def test_no_user(self):
        """
        Make sure nothing breaks if the user wasn't authenticated or was otherwise
        popped somewhere along the pipeline.
        """
        result = pipeline_set_user_roles({}, None)
        self.assertEqual(result, {})


class BearerAuthenticationTests(TestCase):
    """ Tests for the BearerAuthentication class. """

    def setUp(self):
        super(BearerAuthenticationTests, self).setUp()
        self.auth = BearerAuthentication()
        self.factory = APIRequestFactory()

    def _create_request(self, token='12345', token_name='Bearer'):
        """Create request with authorization header. """
        auth_header = '{} {}'.format(token_name, token)
        request = self.factory.get('/', HTTP_AUTHORIZATION=auth_header)
        return request

    def test_authenticate_header(self):
        """The method should return the string Bearer."""
        self.assertEqual(self.auth.authenticate_header(self._create_request()), 'Bearer')

    def test_authenticate_invalid_token(self):
        """If no token is supplied, or if the token contains spaces, the method should raise an exception."""

        # Missing token
        request = self._create_request('')
        self.assertRaises(AuthenticationFailed, self.auth.authenticate, request)

        # Token with spaces
        request = self._create_request('abc 123 456')
        self.assertRaises(AuthenticationFailed, self.auth.authenticate, request)
