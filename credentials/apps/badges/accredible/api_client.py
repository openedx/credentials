import logging

from attrs import asdict
from django.conf import settings
from django.contrib.sites.models import Site

from credentials.apps.badges.accredible.data import AccredibleBadgeData, AccredibleExpireBadgeData
from credentials.apps.badges.accredible.exceptions import AccredibleError
from credentials.apps.badges.accredible.utils import get_accredible_api_base_url
from credentials.apps.badges.base_api_client import BaseBadgeProviderClient
from credentials.apps.badges.models import AccredibleAPIConfig, AccredibleGroup

logger = logging.getLogger(__name__)


class AccredibleAPIClient(BaseBadgeProviderClient):
    """
    A client for interacting with the Accredible API.

    This class provides methods for performing various operations on the Accredible API.
    """

    PROVIDER_NAME = "Accredible"

    def __init__(self, api_config_id: int):
        """
        Initializes a AccredibleAPIClient object.

        Args:
            api_config (AccredibleAPIConfig): Configuration object for the Accredible API.
        """

        self.api_config_id = api_config_id
        self.api_config = self.get_api_config()

    def get_api_config(self) -> AccredibleAPIConfig:
        """
        Returns the API configuration object for the Accredible API.
        """
        try:
            return AccredibleAPIConfig.objects.get(id=self.api_config_id)
        except AccredibleAPIConfig.DoesNotExist:
            raise AccredibleError(f"AccredibleAPIConfig with the id {self.api_config_id} does not exist!")

    def _get_base_api_url(self) -> str:
        return get_accredible_api_base_url(settings)

    def _get_headers(self) -> dict:
        """
        Returns the headers for making API requests to Accredible.
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_config.api_key}",
        }

    def fetch_all_groups(self) -> dict:
        """
        Fetch all groups.
        """
        return self.perform_request("get", "issuer/all_groups")

    def fetch_design_image(self, design_id: int) -> str:
        """
        Fetches the design and return the URL of image.
        """
        design_raw = self.perform_request("get", f"designs/{design_id}")
        return design_raw.get("design", {}).get("rasterized_content_url")

    def issue_badge(self, issue_badge_data: AccredibleBadgeData) -> dict:
        """
        Issues a badge using the Accredible REST API.

        Args:
            issue_badge_data (IssueBadgeData): Data required to issue the badge.
        """
        return self.perform_request("post", "credentials", asdict(issue_badge_data))

    def revoke_badge(self, badge_id, data: AccredibleExpireBadgeData) -> dict:
        """
        Revoke a badge with the given badge ID.

        Args:
            badge_id (str): ID of the badge to revoke.
            data (dict): Additional data for the revocation.
        """
        return self.perform_request("patch", f"credentials/{badge_id}", asdict(data))

    def sync_groups(self, site_id: int) -> int:
        """
        Pull all groups for a given Accredible API config.

        Args:
            site_id (int): ID of the site.

        Returns:
            int: Number of groups synchronized
        """
        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            logger.error(f"Site with the id {site_id} does not exist!")
            raise

        groups_data = self.fetch_all_groups()
        raw_groups = groups_data.get("groups", [])

        all_group_ids = [group.get("id") for group in raw_groups]
        AccredibleGroup.objects.exclude(id__in=all_group_ids).delete()

        for raw_group in raw_groups:
            AccredibleGroup.objects.update_or_create(
                id=raw_group.get("id"),
                api_config=self.api_config,
                defaults={
                    "site": site,
                    "name": raw_group.get("course_name"),
                    "description": raw_group.get("course_description"),
                    "icon": self.fetch_design_image(raw_group.get("primary_design_id")),
                    "created": raw_group.get("created_at"),
                    "state": AccredibleGroup.STATES.active,
                },
            )

        return len(raw_groups)
