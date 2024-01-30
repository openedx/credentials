""" Tests for core models. """

import json
from unittest import mock

import responses
from django.contrib.sites.models import SiteManager
from django.test import TestCase, override_settings
from faker import Faker

from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.core.tests.mixins import JSON, SiteMixin


class UserTests(TestCase):
    """User model tests."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_get_full_name(self):
        """Test that the user model concatenates first and last name if the full name is not set."""
        full_name = "George Costanza"
        user = UserFactory(full_name=full_name)
        self.assertEqual(user.get_full_name(), full_name)

        first_name = "Jerry"
        last_name = "Seinfeld"
        user = UserFactory(full_name=None, first_name=first_name, last_name=last_name)
        expected = f"{first_name} {last_name}"
        self.assertEqual(user.get_full_name(), expected)

        user = UserFactory(full_name=full_name, first_name=first_name, last_name=last_name)
        self.assertEqual(user.get_full_name(), full_name)


class SiteConfigurationTests(SiteMixin, TestCase):
    """Site configuration model tests."""

    def test_str(self):
        """Test the site value for site configuration model."""
        site = SiteFactory(domain="test.org", name="test")
        site_configuration = SiteConfigurationFactory(site=site)
        self.assertEqual(str(site_configuration), site.name)

    def test_clear_site_cache_on_db_write(self):
        """Verify the site cache is cleared whenever a SiteConfiguration instance is
        saved or deleted from the database."""
        with mock.patch.object(SiteManager, "clear_cache") as mock_clear_site_cache:
            sc = SiteConfigurationFactory()
            mock_clear_site_cache.assert_called_once()

            mock_clear_site_cache.reset_mock()
            sc.delete()
            mock_clear_site_cache.assert_called_once()

    def test_user_api_url(self):
        """Verify the User API URL is composed correctly."""
        expected = "{}/api/user/v1/".format(self.site_configuration.lms_url_root.strip("/"))
        self.assertEqual(self.site_configuration.user_api_url, expected)

    def test_name_verification_api_url(self):
        """Verify the Name Verification API URL is composed correctly."""
        expected = "{}/api/edx_name_affirmation/v1/verified_name".format(
            self.site_configuration.lms_url_root.strip("/")
        )
        self.assertEqual(self.site_configuration.name_verification_api_url, expected)

    @responses.activate
    @override_settings(USER_CACHE_TTL=60)
    def test_get_user_api_data_with_cache(self):
        """Verify the method retrieves data from the User API and caches it."""
        username = Faker().user_name()
        user_data = {
            "username": username,
        }
        user_url = f"{self.site_configuration.user_api_url}accounts/{username}"
        responses.add(responses.GET, user_url, body=json.dumps(user_data), content_type=JSON, status=200)

        verification_data = {
            "username": "jdoe",
            "verified_name": "Jonathan Doe",
            "profile_name": "Jon Doe",
            "verification_attempt_id": 123,
            "proctored_exam_attempt_id": None,
            "is_verified": True,
            "use_verified_name_for_certs": False,
        }
        verification_url = f"{self.site_configuration.name_verification_api_url}?username={username}"
        responses.add(
            responses.GET, verification_url, body=json.dumps(verification_data), content_type=JSON, status=200
        )
        self.mock_access_token_response()

        expected_data = user_data
        expected_data["verified_name"] = "Jonathan Doe"
        expected_data["use_verified_name_for_certs"] = False

        actual = self.site_configuration.get_user_api_data(username)
        self.assertEqual(actual, expected_data)
        self.assertEqual(len(responses.calls), 3)

        # Verify the data is cached
        responses.reset()
        actual = self.site_configuration.get_user_api_data(username)
        self.assertEqual(actual, expected_data)
        self.assertEqual(len(responses.calls), 0)

    @responses.activate
    def test_get_user_api_data_with_404(self):
        """Verify the method does not throw exception when non 200 status is returned by verified name API"""
        username = Faker().user_name()
        user_data = {
            "username": username,
        }
        user_url = f"{self.site_configuration.user_api_url}accounts/{username}"
        responses.add(responses.GET, user_url, body=json.dumps(user_data), content_type=JSON, status=200)

        verification_url = f"{self.site_configuration.name_verification_api_url}?username={username}"
        responses.add(responses.GET, verification_url, content_type=JSON, status=404)
        self.mock_access_token_response()

        actual = self.site_configuration.get_user_api_data(username)
        self.assertEqual(actual, user_data)
