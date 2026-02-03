"""
Mixins for Credentials API tests.
"""

import json
from time import time

import jwt
from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory

from credentials.apps.api.v2.serializers import UserCredentialSerializer
from credentials.apps.core.constants import Role
from credentials.apps.core.tests.factories import UserFactory

JWT_AUTH = "JWT_AUTH"


class JwtMixin:
    """Mixin with JWT-related helper functions."""

    JWT_SECRET_KEY = getattr(settings, JWT_AUTH)["JWT_SECRET_KEY"]
    JWT_ISSUER = getattr(settings, JWT_AUTH)["JWT_ISSUER"]
    JWT_AUDIENCE = getattr(settings, JWT_AUTH)["JWT_AUDIENCE"]

    def generate_token(self, payload, secret=None):
        """Generate a JWT token with the provided payload."""
        secret = secret or self.JWT_SECRET_KEY
        token = jwt.encode(payload, secret)
        return token

    def generate_id_token(self, user, admin=False, ttl=1, **overrides):
        """Generate a JWT id_token that looks like the ones currently
        returned by the edx oauth provider."""

        payload = self.default_payload(user=user, admin=admin, ttl=ttl)
        payload.update(overrides)
        return self.generate_token(payload)

    def default_payload(self, user, admin=False, ttl=1):
        """Generate a bare payload, in case tests need to manipulate
        it directly before encoding."""
        now = int(time())

        return {
            "iss": self.JWT_ISSUER,
            "sub": user.pk,
            "aud": self.JWT_AUDIENCE,
            "nonce": "dummy-nonce",
            "exp": now + ttl,
            "iat": now,
            "preferred_username": user.username,
            "administrator": admin,
            "email": user.email,
            "locale": "en",
            "name": user.full_name,
            "given_name": "",
            "family_name": "",
        }


class CredentialViewSetTestsMixin:
    """Base Class for ProgramCredentialViewSetTests and CourseCredentialViewSetTests."""

    list_path = None
    user_credential = None

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.user.groups.add(Group.objects.get(name=Role.ADMINS))
        self.client.force_authenticate(self.user)
        self.request = APIRequestFactory().get("/")

    def assert_permission_required(self, data):
        """
        Ensure access to these APIs is restricted to those with explicit model
        permissions.
        """
        self.client.force_authenticate(user=UserFactory())
        response = self.client.get(self.list_path, data)
        self.assertEqual(response.status_code, 403)

    def assert_list_without_id_filter(self, path, expected, data=None):
        """Helper method used for making request and assertions."""
        response = self.client.get(path, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected)

    def assert_list_with_id_filter(self, data=None, should_exist=True):
        """Helper method used for making request and assertions."""
        expected = self._generate_results(should_exist)
        response = self.client.get(self.list_path, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    def assert_list_with_status_filter(self, data, should_exist=True):
        """Helper method for making request and assertions."""
        expected = self._generate_results(should_exist)
        response = self.client.get(self.list_path, data, expected)
        self.assertEqual(json.loads(response.content), expected)

    def _generate_results(self, exists=True):
        if exists:
            return {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [UserCredentialSerializer(self.user_credential, context={"request": self.request}).data],
            }

        return {"count": 0, "next": None, "previous": None, "results": []}
