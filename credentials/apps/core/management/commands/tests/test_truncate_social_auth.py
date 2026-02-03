"""
Tests for the truncate_social_auth management command
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from social_django.models import UserSocialAuth

from credentials.apps.core.tests.factories import UserFactory, UserSocialAuthFactory

User = get_user_model()

JSON = "application/json"


class TruncateUserSocialAuthTest(TestCase):
    def setUp(self):
        """Create social auth records for test"""
        super().setUp()
        now = datetime.now(timezone.utc)
        long_ago = now - timedelta(days=180)

        self.user_young = UserFactory()
        self.user_old = UserFactory()

        self.auth_young = UserSocialAuthFactory(user_id=self.user_young.id, modified=now)
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = long_ago
            self.auth_old = UserSocialAuthFactory(user_id=self.user_old.id, modified=long_ago)

    @patch("logging.Logger.info")
    def test_delete_old_rows(self, mock_log):
        """verify that only old auth records are deleted."""
        expected = "truncate_social_auth deleted 1 rows"
        auth_records = UserSocialAuth.objects.all()
        self.assertEqual(len(auth_records), 2)

        call_command("truncate_social_auth")

        auth_records = UserSocialAuth.objects.all()
        self.assertEqual(len(auth_records), 1)
        self.assertEqual(auth_records[0], self.auth_young)
        mock_log.assert_called_once_with(expected)

    @patch("logging.Logger.exception")
    def test_exception_handling(self, mock_log):
        """Verify that logging happens if the filter/delete raises an exception"""
        expected = "truncate_social_auth deleted failed"
        with patch("social_django.models.UserSocialAuth.objects.filter", side_effect=Exception("Inconceivable!")):
            call_command("truncate_social_auth")
            mock_log.assert_called_once_with(expected)
