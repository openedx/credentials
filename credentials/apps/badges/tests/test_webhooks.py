from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.test.client import RequestFactory
from faker import Faker

from credentials.apps.badges.credly.api_client import CredlyAPIClient
from credentials.apps.badges.credly.webhooks import CredlyWebhook
from credentials.apps.badges.models import CredlyBadgeTemplate, CredlyOrganization


def get_organization(self, organization_id):  # pylint: disable=unused-argument
    organization = MagicMock(spec=CredlyOrganization)
    organization.uuid = organization_id
    organization.api_key = "test_api_key"
    return organization


def perform_request(self, method, endpoint, data=None):  # pylint: disable=unused-argument
    return {"key": "value"}


class CredlyWebhookTestCase(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.fake = Faker()
        self.organization = CredlyOrganization.objects.create(uuid=self.fake.uuid4(), api_key="test_api_key")

    @patch.object(CredlyAPIClient, "_get_organization", get_organization)
    @patch.object(CredlyAPIClient, "perform_request", perform_request)
    def test_webhook_created_event(self):
        with patch(
            "credentials.apps.badges.credly.webhooks.CredlyWebhook.handle_badge_template_created_event"
        ) as mock_handle:
            req = self.rf.post(
                "/credly/webhook/",
                data={
                    "id": self.fake.uuid4(),
                    "organization_id": self.organization.uuid,
                    "event_type": "badge_template.created",
                    "occurred_at": "2021-01-01T00:00:00Z",
                },
            )
            res = CredlyWebhook.as_view()(req)
            self.assertEqual(res.status_code, 204)
            mock_handle.assert_called_once()

    @patch.object(CredlyAPIClient, "_get_organization", get_organization)
    @patch.object(CredlyAPIClient, "perform_request", perform_request)
    def test_webhook_changed_event(self):
        with patch(
            "credentials.apps.badges.credly.webhooks.CredlyWebhook.handle_badge_template_changed_event"
        ) as mock_handle:
            req = self.rf.post(
                "/credly/webhook/",
                data={
                    "id": self.fake.uuid4(),
                    "organization_id": self.organization.uuid,
                    "event_type": "badge_template.changed",
                    "occurred_at": "2021-01-01T00:00:00Z",
                },
            )
            res = CredlyWebhook.as_view()(req)
            self.assertEqual(res.status_code, 204)
            mock_handle.assert_called_once()

    @patch.object(CredlyAPIClient, "_get_organization", get_organization)
    @patch.object(CredlyAPIClient, "perform_request", perform_request)
    def test_webhook_deleted_event(self):
        with patch(
            "credentials.apps.badges.credly.webhooks.CredlyWebhook.handle_badge_template_deleted_event"
        ) as mock_handle:
            req = self.rf.post(
                "/credly/webhook/",
                data={
                    "id": self.fake.uuid4(),
                    "organization_id": self.fake.uuid4(),
                    "event_type": "badge_template.deleted",
                    "occurred_at": "2021-01-01T00:00:00Z",
                },
            )
            res = CredlyWebhook.as_view()(req)
            self.assertEqual(res.status_code, 204)
            mock_handle.assert_called_once()

    @patch.object(CredlyAPIClient, "_get_organization", get_organization)
    @patch.object(CredlyAPIClient, "perform_request", perform_request)
    def test_webhook_nonexistent_event(self):
        with patch("credentials.apps.badges.credly.webhooks.logger.error") as mock_handle:
            req = self.rf.post(
                "/credly/webhookd/",
                data={
                    "id": self.fake.uuid4(),
                    "organization_id": self.fake.uuid4(),
                    "event_type": "unknown_event",
                    "occurred_at": "2021-01-01T00:00:00Z",
                },
            )
            CredlyWebhook.as_view()(req)
            mock_handle.assert_called_once()

    def test_handle_badge_template_deleted_event(self):
        request_data = {
            "organization_id": "test_organization_id",
            "id": "test_event_id",
            "event_type": "badge_template.deleted",
            "data": {
                "badge_template": {
                    "id": self.fake.uuid4(),
                    "owner": {"id": self.fake.uuid4()},
                    "name": "Test Template",
                    "state": "active",
                    "description": "Test Description",
                    "image_url": "http://example.com/image.png",
                }
            },
        }
        request = self.rf.post("/credly/webhook/", data=request_data)

        CredlyWebhook.handle_badge_template_deleted_event(request, request_data)

        self.assertEqual(CredlyBadgeTemplate.objects.count(), 0)
