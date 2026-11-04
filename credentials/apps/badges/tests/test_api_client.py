# pylint: disable=protected-access
from unittest import mock

import requests
import responses
from attrs import asdict
from django.core.cache import cache
from django.test import TestCase
from faker import Faker
from openedx_events.learning.data import BadgeData, BadgeTemplateData, UserData, UserPersonalData

from credentials.apps.badges.credly.api_client import CredlyAPIClient
from credentials.apps.badges.credly.exceptions import CredlyError
from credentials.apps.badges.exceptions import BadgeProviderError
from credentials.apps.badges.models import BadgeTemplate, CredlyOrganization

TOKEN_URL = "https://sandbox-api.credly.com/oauth/token"


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


class CredlyApiClientOAuthTestCase(TestCase):
    """
    OAuth 2.0 Client Credentials flow of the Credly API client.
    """

    def setUp(self):
        cache.clear()
        self.organization = CredlyOrganization.objects.create(
            uuid=Faker().uuid4(),
            name="oauth_organization",
            oauth_client_id="client-id",
            oauth_client_secret="client-secret",
        )
        self.api_client = CredlyAPIClient(
            "test_organization_id",
            oauth_client_id="client-id",
            oauth_client_secret="client-secret",
        )
        self.cache_key = "credly_oauth_access_token_client-id"

    def tearDown(self):
        cache.clear()

    def test_init_loads_oauth_credentials_from_organization(self):
        api_client = CredlyAPIClient(self.organization.uuid)

        self.assertEqual(api_client.oauth_client_id, "client-id")
        self.assertEqual(api_client.oauth_client_secret, "client-secret")
        self.assertEqual(api_client.organization, self.organization)

    def test_get_headers_uses_bearer_token_for_oauth(self):
        cache.set(self.cache_key, "cached-token")

        headers = self.api_client._get_headers()

        self.assertEqual(headers["Authorization"], "Bearer cached-token")

    def test_get_headers_uses_basic_auth_for_api_key(self):
        api_client = CredlyAPIClient("test_organization_id", api_key="test_api_key")

        headers = api_client._get_headers()

        self.assertEqual(headers["Authorization"], "Basic dGVzdF9hcGlfa2V5")

    def test_get_headers_without_credentials_raises(self):
        api_client = CredlyAPIClient("test_organization_id", api_key="test_api_key")
        api_client.api_key = None

        with self.assertRaises(CredlyError) as cm:
            api_client._get_headers()

        self.assertIn("No valid authentication credentials", str(cm.exception))

    @responses.activate
    def test_get_oauth_token_requests_and_caches_token(self):
        responses.add(responses.POST, TOKEN_URL, json={"access_token": "fresh-token", "expires_in": 7200})

        token = self.api_client._get_oauth_token()

        self.assertEqual(token, "fresh-token")
        self.assertEqual(cache.get(self.cache_key), "fresh-token")
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0].request
        self.assertIn("grant_type=client_credentials", request.body)
        self.assertIn("scope=badge_templates+issued_badges", request.body)
        self.assertTrue(request.headers["Authorization"].startswith("Basic "))

    @responses.activate
    def test_get_oauth_token_uses_cached_token(self):
        cache.set(self.cache_key, "cached-token")

        token = self.api_client._get_oauth_token()

        self.assertEqual(token, "cached-token")
        self.assertEqual(len(responses.calls), 0)

    @responses.activate
    def test_get_oauth_token_force_refresh_bypasses_cache(self):
        cache.set(self.cache_key, "stale-token")
        responses.add(responses.POST, TOKEN_URL, json={"access_token": "fresh-token", "expires_in": 7200})

        token = self.api_client._get_oauth_token(force_refresh=True)

        self.assertEqual(token, "fresh-token")
        self.assertEqual(cache.get(self.cache_key), "fresh-token")

    def test_get_oauth_token_without_credentials_returns_none(self):
        api_client = CredlyAPIClient("test_organization_id", api_key="test_api_key")

        self.assertIsNone(api_client._get_oauth_token())

    @responses.activate
    def test_get_oauth_token_missing_access_token_raises(self):
        responses.add(responses.POST, TOKEN_URL, json={"token_type": "Bearer"})

        with self.assertRaises(CredlyError) as cm:
            self.api_client._get_oauth_token()

        self.assertIn("did not contain access_token", str(cm.exception))
        self.assertIsNone(cache.get(self.cache_key))

    @responses.activate
    def test_get_oauth_token_http_error_raises_credly_error(self):
        responses.add(responses.POST, TOKEN_URL, json={"error": "invalid_client"}, status=401)

        with self.assertRaises(CredlyError) as cm:
            self.api_client._get_oauth_token()

        self.assertIn("Failed to fetch OAuth token", str(cm.exception))

    @responses.activate
    def test_get_oauth_token_network_error_raises_credly_error(self):
        responses.add(responses.POST, TOKEN_URL, body=requests.ConnectionError("boom"))

        with self.assertRaises(CredlyError) as cm:
            self.api_client._get_oauth_token()

        self.assertIn("Failed to fetch OAuth token", str(cm.exception))

    @responses.activate
    def test_get_oauth_token_non_json_response_raises_credly_error(self):
        responses.add(responses.POST, TOKEN_URL, body="<html>Bad gateway</html>", status=200)

        with self.assertRaises(CredlyError) as cm:
            self.api_client._get_oauth_token()

        self.assertIn("non-JSON", str(cm.exception))
        self.assertIsNone(cache.get(self.cache_key))

    @responses.activate
    def test_perform_request_refreshes_token_and_retries_on_401(self):
        cache.set(self.cache_key, "stale-token")
        api_url = "https://sandbox-api.credly.com/v1/organizations/test_organization_id/badge_templates/"
        responses.add(responses.GET, api_url, json={"message": "Unauthorized"}, status=401)
        responses.add(responses.POST, TOKEN_URL, json={"access_token": "fresh-token", "expires_in": 7200})
        responses.add(responses.GET, api_url, json={"data": []}, status=200)

        result = self.api_client.perform_request("get", "badge_templates/")

        self.assertEqual(result, {"data": []})
        self.assertEqual(cache.get(self.cache_key), "fresh-token")
        self.assertEqual(responses.calls[0].request.headers["Authorization"], "Bearer stale-token")
        self.assertEqual(responses.calls[2].request.headers["Authorization"], "Bearer fresh-token")

    @responses.activate
    def test_perform_request_retries_only_once_on_401(self):
        cache.set(self.cache_key, "stale-token")
        api_url = "https://sandbox-api.credly.com/v1/organizations/test_organization_id/badge_templates/"
        responses.add(responses.GET, api_url, json={"message": "Unauthorized"}, status=401)
        responses.add(responses.POST, TOKEN_URL, json={"access_token": "fresh-token", "expires_in": 7200})
        responses.add(responses.GET, api_url, json={"message": "Unauthorized"}, status=401)

        with self.assertRaises(BadgeProviderError) as cm:
            self.api_client.perform_request("get", "badge_templates/")

        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(len(responses.calls), 3)

    @responses.activate
    def test_perform_request_does_not_retry_on_401_with_api_key(self):
        api_client = CredlyAPIClient("test_organization_id", api_key="test_api_key")
        api_url = "https://sandbox-api.credly.com/v1/organizations/test_organization_id/badge_templates/"
        responses.add(responses.GET, api_url, json={"message": "Unauthorized"}, status=401)

        with self.assertRaises(BadgeProviderError):
            api_client.perform_request("get", "badge_templates/")

        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_perform_request_does_not_retry_on_other_errors(self):
        cache.set(self.cache_key, "token")
        api_url = "https://sandbox-api.credly.com/v1/organizations/test_organization_id/badge_templates/"
        responses.add(responses.GET, api_url, json={"message": "Server error"}, status=500)

        with self.assertRaises(BadgeProviderError) as cm:
            self.api_client.perform_request("get", "badge_templates/")

        self.assertEqual(cm.exception.status_code, 500)
        self.assertEqual(len(responses.calls), 1)
