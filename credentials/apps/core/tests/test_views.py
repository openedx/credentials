"""Test core.views."""

import importlib
import sys
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import clear_url_caches, reverse

from credentials.apps.core.constants import Status
from credentials.apps.core.tests.mixins import SiteMixin

User = get_user_model()


class HealthTests(TestCase):
    """Tests of the health endpoint.

    These tests do not rely on SiteMixin, because this endpoint should be site-agnostic.
    """

    def test_all_services_available(self):
        """Test that the endpoint reports when all services are healthy."""
        self._assert_health(200, Status.OK, Status.OK)

    @mock.patch("django.contrib.sites.middleware.get_current_site", mock.Mock(return_value=None))
    @mock.patch("django.db.backends.base.base.BaseDatabaseWrapper.cursor", mock.Mock(side_effect=DatabaseError))
    def test_database_outage(self):
        """Test that the endpoint reports when the database is unavailable."""
        self._assert_health(503, Status.UNAVAILABLE, Status.UNAVAILABLE)

    def _assert_health(self, status_code, overall_status, database_status):
        """Verify that the response matches expectations."""
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response["content-type"], "application/json")

        expected_data = {"overall_status": overall_status, "detailed_status": {"database_status": database_status}}

        self.assertJSONEqual(response.content.decode("utf8"), expected_data)


class AutoAuthTests(SiteMixin, TestCase):
    """Auto Auth view tests."""

    AUTO_AUTH_PATH = reverse("auto_auth")

    @override_settings(ENABLE_AUTO_AUTH=False)
    def test_setting_disabled(self):
        """When the ENABLE_AUTO_AUTH setting is False, the view should raise a 404."""
        response = self.client.get(self.AUTO_AUTH_PATH)
        self.assertEqual(response.status_code, 404)

    @override_settings(ENABLE_AUTO_AUTH=True)
    def test_setting_enabled(self):
        """
        When ENABLE_AUTO_AUTH is set to True, the view should create and authenticate
        a new User with superuser permissions.
        """
        original_user_count = User.objects.count()
        response = self.client.get(self.AUTO_AUTH_PATH)

        # Verify that a redirect has occurred and that a new user has been created
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), original_user_count + 1)

        # Get the latest user
        user = User.objects.latest()

        # Verify that the user is logged in and that their username has the expected prefix
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(user.username.startswith(settings.AUTO_AUTH_USERNAME_PREFIX))

        # Verify that the user has superuser permissions
        self.assertTrue(user.is_superuser)


class SiteViewTests(SiteMixin, TestCase):
    """Tests for the base site views."""

    def _reload_urlconf(self):
        """Helper method to reload url config."""
        importlib.reload(sys.modules[settings.ROOT_URLCONF])
        clear_url_caches()

    @override_settings(DEBUG=True)
    def test_500(self):
        # Since the the url for the custom 500 view is included only for debug
        # mode so we need to set the debug mode and reload the django urls
        # config for adding the 500 view url
        self._reload_urlconf()

        response = self.client.get(reverse("500"))
        self.assertEqual(response.status_code, 500)
