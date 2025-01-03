from unittest import mock

import faker
from django.core.management import call_command
from django.test import TestCase

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
