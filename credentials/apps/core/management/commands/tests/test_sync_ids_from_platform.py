"""
Tests for the sync_lms_user_ids management command
"""

import json

import responses
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin

User = get_user_model()

JSON = "application/json"


class LmsIdSyncTests(SiteMixin, TestCase):
    def setUp(self):
        """
        Create users with no lms_id
        """
        super().setUp()
        self.user = UserFactory(is_superuser=True)

    def mock_account_api_response(self, status=200):
        url = self.site.siteconfiguration.user_api_url + "accounts"
        body = [{"username": "user1", "id": 1}]
        responses.add(
            responses.GET,
            url,
            body=json.dumps(body),
            content_type=JSON,
            status=status,
            match_querystring=False,
        )

    @responses.activate
    def test_update_ids(self):
        """verify all ids were updated"""
        UserFactory(username="user1", lms_user_id=None)

        self.mock_access_token_response()
        self.mock_account_api_response()
        call_command("sync_ids_from_platform", verbose=True)

        user = User.objects.get(lms_user_id=1)
        print(f"fetched user: {user.username}, id {user.lms_user_id}")
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.lms_user_id, 1, "User ID was not updated")

    @responses.activate
    def test_update_ids_404(self):
        user = UserFactory(username="user1", lms_user_id=None)

        self.mock_access_token_response()
        user_url = self.site.siteconfiguration.user_api_url + "accounts"
        responses.add(
            responses.GET,
            user_url,
            content_type=JSON,
            status=404,
            match_querystring=False,
        )
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.lms_user_id, None, "User ID was updated unexpectedly")

    @responses.activate
    def test_update_site(self):
        """verify all ids were updated"""
        UserFactory(username="user1", lms_user_id=None)

        self.mock_access_token_response()
        self.mock_account_api_response()
        print(f"\n\n==>  site_id from configuration: {self.site_configuration.site_id}/n/n")
        call_command("sync_ids_from_platform", verbose=True, site_id=self.site_configuration.site_id)

        user = User.objects.get(lms_user_id=1)
        print(f"fetched user: {user.username}, id {user.lms_user_id}")
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.lms_user_id, 1, "User ID was not updated")

    @responses.activate
    def test_dry_run(self):
        """verify ids were NOT updated"""
        UserFactory(username="user1", lms_user_id=None)

        self.mock_access_token_response()
        self.mock_account_api_response()
        call_command("sync_ids_from_platform", dry_run=True, verbose=True, limit=0, pause_secs=0)

        user = User.objects.get(username="user1")
        print(f"fetched user: {user.username}, id {user.lms_user_id}")
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.lms_user_id, None, "User ID was updated in dry_run")
