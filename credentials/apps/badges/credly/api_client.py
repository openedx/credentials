import base64
import logging
import time
from functools import lru_cache
from urllib.parse import urljoin

import requests  # pylint: disable=unused-import
from attrs import asdict
from django.core.cache import cache
from django.conf import settings
from django.contrib.sites.models import Site

from credentials.apps.badges.base_api_client import BaseBadgeProviderClient
from credentials.apps.badges.credly.exceptions import CredlyError
from credentials.apps.badges.credly.utils import get_credly_api_base_url
from credentials.apps.badges.models import CredlyBadgeTemplate, CredlyOrganization

logger = logging.getLogger(__name__)


class CredlyAPIClient(BaseBadgeProviderClient):
    """
    A client for interacting with the Credly API.

    This class provides methods for performing various operations on the Credly API,
    such as fetching organization details, fetching badge templates, issuing badges,
    and revoking badges.
    """

    PROVIDER_NAME = "Credly"

    def __init__(
        self,
        organization_id,
        api_key=None,
        oauth_client_id=None,
        oauth_client_secret=None,
    ):  # pylint: disable=super-init-not-called
        """
        Initializes a CredlyRestAPI object.

        Args:
            organization_id (str, uuid): ID of the organization.
            api_key (str): Optional legacy API key of the organization.
            oauth_client_id (str): Optional OAuth Client ID.
            oauth_client_secret (str): Optional OAuth Client Secret.
        """
        self.organization_id = organization_id
        self.organization = None

        if not (api_key or (oauth_client_id and oauth_client_secret)):
            self.organization = self._get_organization(organization_id)
            api_key = self.organization.api_key
            oauth_client_id = getattr(self.organization, "oauth_client_id", None)
            oauth_client_secret = getattr(self.organization, "oauth_client_secret", None)

        self.api_key = api_key
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret

    def _get_base_api_url(self):
        return urljoin(get_credly_api_base_url(settings), f"organizations/{self.organization_id}/")

    def _get_organization(self, organization_id):
        """
        Check if Credly Organization with provided ID exists.
        """
        try:
            organization = CredlyOrganization.objects.get(uuid=organization_id)
            return organization
        except CredlyOrganization.DoesNotExist:
            raise CredlyError(f"CredlyOrganization with the uuid {organization_id} does not exist!")

    def _get_oauth_token(self):
        """
        Obtains a Bearer Access Token from Credly OAuth endpoint using Client Credentials grant.
        """
        if not (self.oauth_client_id and self.oauth_client_secret):
            return None

        cache_key = f"credly_oauth_access_token_{self.oauth_client_id}"
        token = cache.get(cache_key)

        if not token:
            token_url = urljoin(get_credly_api_base_url(settings), "/oauth/token")

            try:
                payload = {
                    "grant_type": "client_credentials",
                    "scope": "badge_templates issued_badges",
                }

                response = requests.post(
                    token_url,
                    data=payload,
                    auth=(self.oauth_client_id, self.oauth_client_secret),
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()

                token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)

                if not token:
                    raise CredlyError(f"Credly response did not contain access_token: {data}")

                cache.set(cache_key, token, timeout=max(expires_in - 60, 60))

            except requests.RequestException as exc:
                raise CredlyError(f"Failed to fetch OAuth token from Credly: {str(exc)}") from exc

        return token

    def _get_headers(self):
        """
        Returns the headers for making API requests to Credly.
        Supports both OAuth Bearer Tokens and legacy Basic Auth API Keys.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.oauth_client_id and self.oauth_client_secret:
            bearer_token = self._get_oauth_token()
            headers["Authorization"] = f"Bearer {bearer_token}"

        elif self.api_key:
            headers["Authorization"] = f"Basic {self._build_authorization_token()}"

        else:
            raise CredlyError("No valid authentication credentials (OAuth or API Key) available for Credly.")

        return headers

    @lru_cache
    def _build_authorization_token(self):
        """
        Build the authorization token for the Credly API (Legacy).

        Returns:
            str: Authorization token.
        """
        if not self.api_key:
            return ""
        return base64.b64encode(self.api_key.encode("ascii")).decode("ascii")

    def fetch_organization(self):
        """
        Fetches Credly Organization data.
        """
        return self.perform_request("get", "")

    def fetch_badge_templates(self):
        """
        Fetches the badge templates from the Credly API.
        """
        results = []
        url = f"badge_templates/?filter=state::{CredlyBadgeTemplate.STATES.active}"
        response = self.perform_request("get", url)
        results.extend(response.get("data", []))

        metadata = response.get("metadata", {})
        total_pages = metadata.get("total_pages", 1)
        next_page_url = metadata.get("next_page_url")

        # Loop through all remaining pages based on the total_pages value.
        # For each iteration, fetch data using the 'next_page_url' provided by the API,
        # append the results to the main list, and update the URL for the next request.
        # The loop stops when there are no more pages to retrieve.
        for _ in range(2, total_pages + 1):
            if not next_page_url:
                break

            time.sleep(0.2)

            for attempt in range(3):
                try:
                    response = self.perform_request("get", next_page_url)
                    break
                except (requests.Timeout, requests.ConnectionError) as exc:
                    sleep_time = 0.5 * (2**attempt)
                    time.sleep(sleep_time)

                    if attempt == 2:
                        raise CredlyError(f"Failed to fetch page due to network error: {exc}")

            results.extend(response.get("data", []))
            next_page_url = response.get("metadata", {}).get("next_page_url")

        return {"data": results}

    def fetch_event_information(self, event_id):
        """
        Fetches the event information from the Credly API.

        Args:
            event_id (str): ID of the event.
        """
        return self.perform_request("get", f"events/{event_id}/")

    def issue_badge(self, issue_badge_data):
        """
        Issues a badge using the Credly REST API.

        Args:
            issue_badge_data (IssueBadgeData): Data required to issue the badge.
        """
        return self.perform_request("post", "badges/", asdict(issue_badge_data))

    def revoke_badge(self, badge_id, data=None):
        """
        Revoke a badge with the given badge ID.

        Args:
            badge_id (str): ID of the badge to revoke.
            data (dict): Additional data for the revocation.
        """
        return self.perform_request("put", f"badges/{badge_id}/revoke/", data=data)

    def sync_organization_badge_templates(self, site_id):
        """
        Pull active badge templates for a given Credly Organization.

        Args:
            site_id (int): ID of the site.

        Returns:
            int | None: processed items.
        """
        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            logger.error(f"Site with the id {site_id} does not exist!")
            raise

        if not self.organization:
            self.organization = self._get_organization(self.organization_id)

        badge_templates_data = self.fetch_badge_templates()
        raw_badge_templates = badge_templates_data.get("data", [])

        for raw_badge_template in raw_badge_templates:
            CredlyBadgeTemplate.objects.update_or_create(
                uuid=raw_badge_template.get("id"),
                organization=self.organization,
                defaults={
                    "site": site,
                    "name": raw_badge_template.get("name"),
                    "state": raw_badge_template.get("state"),
                    "description": raw_badge_template.get("description"),
                    "icon": raw_badge_template.get("image_url"),
                },
            )

        return len(raw_badge_templates)
