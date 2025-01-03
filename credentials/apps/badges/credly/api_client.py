import base64
import logging
from functools import lru_cache
from urllib.parse import urljoin

import requests  # pylint: disable=unused-import
from attrs import asdict
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

    def __init__(self, organization_id, api_key=None):  # pylint: disable=super-init-not-called
        """
        Initializes a CredlyRestAPI object.

        Args:
            organization_id (str, uuid): ID of the organization.
            api_key (str): optional ID of the organization.
        """
        if api_key is None:
            self.organization = self._get_organization(organization_id)
            api_key = self.organization.api_key

        self.api_key = api_key
        self.organization_id = organization_id

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

    def _get_headers(self):
        """
        Returns the headers for making API requests to Credly.
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._build_authorization_token()}",
        }

    @lru_cache
    def _build_authorization_token(self):
        """
        Build the authorization token for the Credly API.

        Returns:
            str: Authorization token.
        """
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
        return self.perform_request("get", f"badge_templates/?filter=state::{CredlyBadgeTemplate.STATES.active}")

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
