from datetime import timedelta
from unittest import mock

import faker
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from credentials.apps.badges.models import AccredibleAPIConfig, CredlyOrganization


class TestSyncOrganizationBadgeTemplatesCommand(TestCase):
    def setUp(self):
        self.faker = faker.Faker()
        self.credly_organization = CredlyOrganization.objects.create(
            uuid=self.faker.uuid4(), api_key=self.faker.uuid4(), name=self.faker.word()
        )
        CredlyOrganization.objects.bulk_create([CredlyOrganization(uuid=self.faker.uuid4()) for _ in range(5)])

    @mock.patch("credentials.apps.badges.management.commands.sync_organization_badge_templates.CredlyAPIClient")
    def test_handle_no_arguments(self, mock_credly_api_client):
        call_command("sync_organization_badge_templates")
        self.assertEqual(mock_credly_api_client.call_count, 6)
        self.assertEqual(mock_credly_api_client.return_value.sync_organization_badge_templates.call_count, 6)

    @mock.patch("credentials.apps.badges.management.commands.sync_organization_badge_templates.CredlyAPIClient")
    def test_handle_with_organization_id(self, mock_credly_api_client):
        call_command("sync_organization_badge_templates", "--organization_id", self.credly_organization.uuid)
        mock_credly_api_client.assert_called_once_with(self.credly_organization.uuid)
        mock_credly_api_client.return_value.sync_organization_badge_templates.assert_called_once_with(1)


class TestSyncAccredibleGroupsCommand(TestCase):
    def setUp(self):
        self.faker = faker.Faker()
        self.api_config = AccredibleAPIConfig.objects.create(api_key=self.faker.uuid4(), name=self.faker.word())
        AccredibleAPIConfig.objects.bulk_create([AccredibleAPIConfig(api_key=self.faker.uuid4()) for _ in range(5)])

    @mock.patch("credentials.apps.badges.management.commands.sync_accredible_groups.AccredibleAPIClient")
    def test_handle_no_arguments(self, mock_accredible_api_client):
        call_command("sync_accredible_groups")
        self.assertEqual(mock_accredible_api_client.call_count, AccredibleAPIConfig.objects.all().count())
        self.assertEqual(
            mock_accredible_api_client.return_value.sync_groups.call_count, AccredibleAPIConfig.objects.all().count()
        )

    @mock.patch("credentials.apps.badges.management.commands.sync_accredible_groups.AccredibleAPIClient")
    def test_handle_with_api_config_id(self, mock_accredible_api_client):
        call_command("sync_accredible_groups", "--api_config_id", self.api_config.id)
        mock_accredible_api_client.assert_called_once_with(1)
        mock_accredible_api_client.return_value.sync_groups.assert_called_once_with(1)


@mock.patch(
    "credentials.apps.badges.management.commands.refresh_credly_authorization_tokens.CredlyAPIClient"
)
class TestRefreshCredlyAuthorizationTokensCommand(TestCase):
    """
    Tests for the ``refresh_credly_authorization_tokens`` management command.

    Token expiration is derived from ``authorization_token_updated_at`` plus the 180-day lifetime, so
    a token with ``days_left`` remaining is simulated by backdating that field accordingly. A 12-hour
    buffer is added to keep the truncated day count off threshold boundaries.
    """

    COMMAND = "refresh_credly_authorization_tokens"

    def setUp(self):
        self.faker = faker.Faker()

    def _make_organization(self, days_left=None):
        organization = CredlyOrganization.objects.create(
            uuid=self.faker.uuid4(), api_key=self.faker.uuid4(), name=self.faker.word()
        )
        if days_left is not None:
            lifetime = CredlyOrganization.AUTHORIZATION_TOKEN_LIFETIME
            organization.authorization_token_updated_at = (
                timezone.now() - lifetime + timedelta(days=days_left, hours=12)
            )
            organization.save()
        # Reload so ``organization.uuid`` is a UUID instance, as the command sees it when querying the DB.
        organization.refresh_from_db()
        return organization

    def test_healthy_token_is_not_rotated(self, mock_credly_api_client):
        self._make_organization(days_left=100)
        call_command(self.COMMAND)
        mock_credly_api_client.return_value.rotate_authorization_token.assert_not_called()

    def test_token_in_warning_window_is_not_rotated(self, mock_credly_api_client):
        self._make_organization(days_left=20)
        with self.assertLogs(
            "credentials.apps.badges.management.commands.refresh_credly_authorization_tokens",
            level="WARNING",
        ) as logs:
            call_command(self.COMMAND)
        mock_credly_api_client.return_value.rotate_authorization_token.assert_not_called()
        self.assertTrue(any("expires in" in message for message in logs.output))

    def test_token_close_to_expiry_is_rotated(self, mock_credly_api_client):
        organization = self._make_organization(days_left=2)
        call_command(self.COMMAND)
        mock_credly_api_client.assert_called_once_with(organization.uuid)
        mock_credly_api_client.return_value.rotate_authorization_token.assert_called_once_with()

    def test_token_without_dates_is_warned_not_rotated(self, mock_credly_api_client):
        self._make_organization(days_left=None)
        with self.assertLogs(
            "credentials.apps.badges.management.commands.refresh_credly_authorization_tokens",
            level="WARNING",
        ):
            call_command(self.COMMAND)
        mock_credly_api_client.return_value.rotate_authorization_token.assert_not_called()

    def test_force_rotates_regardless_of_expiry(self, mock_credly_api_client):
        organization = self._make_organization(days_left=100)
        call_command(self.COMMAND, "--force")
        mock_credly_api_client.assert_called_once_with(organization.uuid)
        mock_credly_api_client.return_value.rotate_authorization_token.assert_called_once_with()

    def test_organization_id_limits_scope(self, mock_credly_api_client):
        target = self._make_organization(days_left=2)
        self._make_organization(days_left=2)
        call_command(self.COMMAND, "--organization_id", target.uuid)
        mock_credly_api_client.assert_called_once_with(target.uuid)
