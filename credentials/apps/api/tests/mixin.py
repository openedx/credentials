"""Mixin class for authentication."""
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from credentials.apps.api.tests.factories import UserFactory


class AuthClientMixin(object):
    """Mixin useful for getting APIClient objects in tests."""

    def get_api_client(self, permission_code=None):
        """
        Helper for concisely obtaining a `rest_framework.test.APIClient` instance,
        authenticated with a user having specific model level permissions.

        Arguments:
            permission_code (string): Permission codename for specific permission

        Returns:
            returns authenticated APIClient object with specific permissions, if no
            permission provided then it will returns default object.
        """
        client = APIClient()
        user = UserFactory.create()
        if permission_code:
            # pylint: disable=maybe-no-member
            user.user_permissions.add(Permission.objects.get(codename=permission_code))
            client.force_authenticate(user)

        return client
