"""
Tests for the make_is_active_match_platform management command
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


class IsActiveMatchSyncTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user_active = UserFactory(username="is_active", is_active=True, id=2)
        self.user_inactive = UserFactory(username="is_inactive", is_active=False, id=3)

    def mock_account_api_response(
        self,
        user1_is_active_on_lms: bool,
        user2_is_active_on_lms: bool,
        status: int = 200,
    ):
        url = self.site.siteconfiguration.user_api_url + "accounts"
        user1_active_response = {"username": "is_active", "is_active": user1_is_active_on_lms, "id": 2}
        user2_active_response = {"username": "is_inactive", "is_active": user2_is_active_on_lms, "id": 3}
        body = [user1_active_response, user2_active_response]
        responses.add(
            responses.GET,
            url,
            body=json.dumps(body),
            content_type=JSON,
            status=status,
            match_querystring=False,
        )

    @responses.activate
    def test_unchanged_if_is_active_matches(self):
        """Test nothing changes if is_active matches on LMS and Credentials."""
        self.mock_access_token_response()
        self.mock_account_api_response(True, False)

        user_active = User.objects.get(username="is_active")
        user_inactive = User.objects.get(username="is_inactive")

        call_command("make_is_active_match_platform", verbose=True)

        self.assertTrue(user_active.is_active)
        self.assertFalse(user_inactive.is_active)

    @responses.activate
    def test_changes_only_false_to_true(self):
        """Test that a mismatch changes False to True, but not vice versa, on mismatch between credentials and LMS."""
        self.mock_access_token_response()
        self.mock_account_api_response(False, True)
        call_command("make_is_active_match_platform", verbose=True)

        user_active = User.objects.get(username="is_active")
        user_inactive = User.objects.get(username="is_inactive")
        self.assertTrue(user_active.is_active)
        self.assertTrue(user_inactive.is_active)

    @responses.activate
    def test_update_does_nothing_on_404(self):
        """Test that nothing changes if the response is a 404"""
        self.mock_access_token_response()
        self.mock_account_api_response(False, True, status=404)
        call_command("make_is_active_match_platform", verbose=True)

        user_active = User.objects.get(username="is_active")
        user_inactive = User.objects.get(username="is_inactive")
        self.assertTrue(user_active.is_active)
        self.assertFalse(user_inactive.is_active)

    @responses.activate
    def test_update_does_nothing_if_learner_missing_on_lms(self):
        """Test that nothing changes if the learner isn't found on the LMS"""
        self.mock_access_token_response()
        self.mock_account_api_response(False, True, status=404)

        UserFactory(username="lms_absent_is_active", is_active=True, id=30)
        UserFactory(username="lms_absent_is_inactive", is_active=False, id=40)
        call_command("make_is_active_match_platform", verbose=True)

        user_active = User.objects.get(username="lms_absent_is_active")
        user_inactive = User.objects.get(username="lms_absent_is_inactive")
        self.assertTrue(user_active.is_active)
        self.assertFalse(user_inactive.is_active)

    @responses.activate
    def test_update_site(self):
        """Test that the command works as expected with the site ID given."""
        self.mock_access_token_response()
        self.mock_account_api_response(False, True)
        call_command("make_is_active_match_platform", verbose=True, site_id=self.site_configuration.site_id)

        user_active = User.objects.get(username="is_active")
        user_inactive = User.objects.get(username="is_inactive")
        self.assertTrue(user_active.is_active)
        self.assertTrue(user_inactive.is_active)

    @responses.activate
    def test_dry_run(self):
        """verify nothing changes on a dry run"""
        self.mock_access_token_response()
        self.mock_account_api_response(False, True, status=404)
        call_command("make_is_active_match_platform", dry_run=True, verbose=True, pause_secs=0)

        user_active = User.objects.get(username="is_active")
        user_inactive = User.objects.get(username="is_inactive")
        self.assertTrue(user_active.is_active)
        self.assertFalse(user_inactive.is_active)
