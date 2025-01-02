from unittest import mock

from attrs import asdict
from django.test import TestCase

from credentials.apps.badges.accredible.api_client import AccredibleAPIClient
from credentials.apps.badges.accredible.data import (
    AccredibleBadgeData,
    AccredibleCredential,
    AccredibleExpireBadgeData,
    AccredibleExpiredCredential,
    AccredibleRecipient,
)
from credentials.apps.badges.models import AccredibleAPIConfig, AccredibleGroup


class AccredibleAPIClientTestCase(TestCase):
    def setUp(self):
        self.api_config = AccredibleAPIConfig.objects.create(
            api_key="test-api-key",
            name="test_config",
        )
        self.api_client = AccredibleAPIClient(self.api_config.id)
        self.badge_data = AccredibleBadgeData(
            credential=AccredibleCredential(
                recipient=AccredibleRecipient(name="Test name", email="test_name@test.com"),
                group_id=123,
                name="Test Badge",
                issued_on="2021-01-01 00:00:00 +0000",
                complete=True,
            )
        )
        self.expire_badge_data = AccredibleExpireBadgeData(
            credential=AccredibleExpiredCredential(expired_on="2021-01-01 00:00:00 +0000")
        )

    def test_fetch_all_groups(self):
        with mock.patch.object(AccredibleAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"groups": ["group1", "group2"]}
            result = self.api_client.fetch_all_groups()
            mock_perform_request.assert_called_once_with("get", "issuer/all_groups")
            self.assertEqual(result, {"groups": ["group1", "group2"]})

    def test_fetch_design_image(self):
        design_id = 123
        with mock.patch.object(AccredibleAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"design": {"rasterized_content_url": "url"}}
            result = self.api_client.fetch_design_image(design_id)
            mock_perform_request.assert_called_once_with("get", f"designs/{design_id}")
            self.assertEqual(result, "url")

    def test_issue_badge(self):
        with mock.patch.object(AccredibleAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"badge": "issued"}
            result = self.api_client.issue_badge(self.badge_data)
            mock_perform_request.assert_called_once_with("post", "credentials", asdict(self.badge_data))
            self.assertEqual(result, {"badge": "issued"})

    def test_revoke_badge(self):
        badge_id = 123
        with mock.patch.object(AccredibleAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"badge": "revoked"}
            result = self.api_client.revoke_badge(badge_id, self.expire_badge_data)
            mock_perform_request.assert_called_once_with(
                "patch", f"credentials/{badge_id}", asdict(self.expire_badge_data)
            )
            self.assertEqual(result, {"badge": "revoked"})

    def test_sync_groups(self):
        AccredibleGroup.objects.create(
            id=777,
            api_config=self.api_config,
            name="old_name",
            description="old_desc",
            icon="old_icon",
            site_id=1,
        )
        with mock.patch.object(AccredibleAPIClient, "fetch_all_groups") as mock_fetch_all_groups, mock.patch.object(
            AccredibleAPIClient, "fetch_design_image"
        ) as mock_fetch_design_image:
            mock_fetch_all_groups.return_value = {
                "groups": [{"id": 1, "course_name": "name", "course_description": "desc", "primary_design_id": 123}]
            }
            mock_fetch_design_image.return_value = "url"

            self.assertEqual(AccredibleGroup.objects.filter(id=777).exists(), True)
            result = self.api_client.sync_groups(1)
            mock_fetch_all_groups.assert_called_once()
            mock_fetch_design_image.assert_called_once_with(123)
            self.assertEqual(result, 1)
            self.assertEqual(AccredibleGroup.objects.count(), 1)
            self.assertEqual(AccredibleGroup.objects.first().name, "name")
            self.assertEqual(AccredibleGroup.objects.first().description, "desc")
            self.assertEqual(AccredibleGroup.objects.first().icon, "url")
            self.assertEqual(AccredibleGroup.objects.first().api_config, self.api_config)
            self.assertEqual(AccredibleGroup.objects.filter(id=777).exists(), False)
