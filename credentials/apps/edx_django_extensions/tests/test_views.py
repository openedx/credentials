from unittest import mock

from django.contrib import messages
from django.test import TestCase
from django.urls import reverse

from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin


class ManagementViewTests(SiteMixin, TestCase):
    path = reverse("management:index")

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    def get_response_messages(self, response):
        return list(response.context["messages"])

    def assert_message_count(self, response, expected):
        """Asserts the expected number of messages are set."""
        _messages = self.get_response_messages(response)
        self.assertEqual(len(_messages), expected)

    def assert_first_message(self, response, expected_level, expected_msg):
        message = self.get_response_messages(response)[0]
        self.assertEqual(message.message, expected_msg)
        self.assertEqual(message.level, expected_level)

    def test_login_required(self):
        """Verify the view requires login."""
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)

    def test_superuser_required(self):
        """Verify the view is not accessible to non-superusers."""
        self.client.logout()
        user = UserFactory()
        self.client.login(username=user.username, password=USER_PASSWORD)
        response = self.client.get(self.path)

        expected_code = 403

        self.assertEqual(response.status_code, expected_code)

    def test_invalid_action(self):
        """Verify the view responds with an error message if an invalid action is posted."""
        response = self.client.post(self.path, {"action": ""})
        self.assertEqual(response.status_code, 200)
        self.assert_message_count(response, 1)
        self.assert_first_message(response, messages.ERROR, " is not a valid action.")

    @mock.patch("logging.Logger.info")
    @mock.patch("django.core.cache.cache.clear")
    def test_cache_clear(self, mock_cache_clear, mock_log_info):
        """Verify the view clears the cache when the clear_cache action is posted."""
        response = self.client.post(self.path, {"action": "clear_cache"})
        self.assertEqual(response.status_code, 200)
        self.assert_message_count(response, 1)
        self.assert_first_message(response, messages.SUCCESS, "Cache cleared.")
        mock_cache_clear.assert_called_once()
        mock_log_info.assert_called_once_with("Cache cleared by %s.", self.user.username)
