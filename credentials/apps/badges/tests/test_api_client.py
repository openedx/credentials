from unittest import mock

from attrs import asdict
from django.test import TestCase
from faker import Faker
from openedx_events.learning.data import BadgeData, BadgeTemplateData, UserData, UserPersonalData

from credentials.apps.badges.credly.api_client import CredlyAPIClient
from credentials.apps.badges.credly.exceptions import CredlyError
from credentials.apps.badges.models import BadgeTemplate, CredlyOrganization


class CredlyApiClientTestCase(TestCase):
    def setUp(self):
        fake = Faker()
        self.api_client = CredlyAPIClient("test_organization_id", "test_api_key")
        self.badge_data = BadgeData(
            uuid=fake.uuid4(),
            user=UserData(
                id=1,
                is_active=True,
                pii=UserPersonalData(username="test_user", email="test_email@mail.com", name="Test User"),
            ),
            template=BadgeTemplateData(
                uuid=fake.uuid4(),
                name="Test Badge",
                origin="Credly",
                description="Test Badge Description",
                image_url="https://test.com/image.png",
            ),
        )
        self.organization = CredlyOrganization.objects.create(
            uuid=fake.uuid4(), api_key="test-api-key", name="test_organization"
        )

    def test_get_organization_nonexistent(self):
        with mock.patch("credentials.apps.badges.credly.api_client.CredlyOrganization.objects.get") as mock_get:
            mock_get.side_effect = CredlyOrganization.DoesNotExist
            with self.assertRaises(CredlyError) as cm:
                CredlyAPIClient("nonexistent_organization_id")
            self.assertEqual(
                str(cm.exception),
                "CredlyOrganization with the uuid nonexistent_organization_id does not exist!",
            )

    def test_perform_request(self):
        with mock.patch("credentials.apps.badges.credly.api_client.requests.request") as mock_request:
            mock_response = mock.Mock()
            mock_response.json.return_value = {"key": "value"}
            mock_request.return_value = mock_response
            result = self.api_client.perform_request("GET", "/api/endpoint")
            mock_request.assert_called_once_with(
                "GET",
                "https://sandbox-api.credly.com/api/endpoint",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Basic dGVzdF9hcGlfa2V5",
                },
                json=None,
                timeout=10,
            )
            self.assertEqual(result, {"key": "value"})

    def test_fetch_organization(self):
        with mock.patch.object(CredlyAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"organization": "data"}
            result = self.api_client.fetch_organization()
            mock_perform_request.assert_called_once_with("get", "")
            self.assertEqual(result, {"organization": "data"})

    def test_fetch_badge_templates(self):
        with mock.patch.object(CredlyAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {
                "data": ["template1", "template2"],
                "metadata": {"total_pages": 1},
            }
            result = self.api_client.fetch_badge_templates()
            mock_perform_request.assert_called_once_with("get", "badge_templates/?filter=state::active")
            self.assertEqual(result, {"data": ["template1", "template2"]})

    def test_fetch_event_information(self):
        event_id = "event123"
        with mock.patch.object(CredlyAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"event": "data"}
            result = self.api_client.fetch_event_information(event_id)
            mock_perform_request.assert_called_once_with("get", f"events/{event_id}/")
            self.assertEqual(result, {"event": "data"})

    def test_issue_badge(self):
        issue_badge_data = self.badge_data
        with mock.patch.object(CredlyAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"badge": "issued"}
            result = self.api_client.issue_badge(issue_badge_data)
            mock_perform_request.assert_called_once_with("post", "badges/", asdict(issue_badge_data))
            self.assertEqual(result, {"badge": "issued"})

    def test_revoke_badge(self):
        badge_id = "badge123"
        data = {"data": "value"}
        with mock.patch.object(CredlyAPIClient, "perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"badge": "revoked"}
            result = self.api_client.revoke_badge(badge_id, data)
            mock_perform_request.assert_called_once_with("put", f"badges/{badge_id}/revoke/", data=data)
            self.assertEqual(result, {"badge": "revoked"})

    def test_sync_organization_badge_templates(self):
        with mock.patch.object(CredlyAPIClient, "fetch_badge_templates") as mock_fetch_badge_templates:
            mock_fetch_badge_templates.return_value = {
                "data": [
                    {
                        "id": Faker().uuid4(),
                        "name": "Badge Template 1",
                        "state": "active",
                        "description": "Badge Template 1 Description",
                    },
                    {
                        "id": Faker().uuid4(),
                        "name": "Badge Template 2",
                        "state": "active",
                        "description": "Badge Template 2 Description",
                    },
                ]
            }
            api_client = CredlyAPIClient(self.organization.uuid)
            result = api_client.sync_organization_badge_templates(1)
            mock_fetch_badge_templates.assert_called_once()
            self.assertEqual(result, 2)
            badge_templates = BadgeTemplate.objects.all()
            self.assertEqual(badge_templates.count(), 2)
            self.assertEqual(badge_templates[0].name, "Badge Template 1")
