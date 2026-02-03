import logging

from django.core.management.base import BaseCommand

from credentials.apps.badges.credly.api_client import CredlyAPIClient
from credentials.apps.badges.models import CredlyOrganization

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync badge templates for a specific organization or all organizations"

    def add_arguments(self, parser):
        parser.add_argument("--site_id", type=int, help="Site ID.")
        parser.add_argument("--organization_id", type=str, help="UUID of the organization.")

    def handle(self, *args, **options):
        """
        Sync badge templates for a specific organization or all organizations.

        Usage:
            site_id=1
            org_id=c117c179-81b1-4f7e-a3a1-e6ae30568c13

            ./manage.py sync_organization_badge_templates --site_id $site_id
            ./manage.py sync_organization_badge_templates --site_id $site_id --organization_id $org_id
        """
        DEFAULT_SITE_ID = 1
        organizations_to_sync = []

        site_id = options.get("site_id")
        organization_id = options.get("organization_id")

        if site_id is None:
            logger.warning(f"Side ID wasn't provided: assuming site_id = {DEFAULT_SITE_ID}")
            site_id = DEFAULT_SITE_ID

        if organization_id:
            organizations_to_sync.append(organization_id)
            logger.info(f"Syncing badge templates for the single organization: {organization_id}")
        else:
            organizations_to_sync = CredlyOrganization.get_all_organization_ids()
            logger.info(
                "Organization ID wasn't provided: syncing badge templates for all organizations - "
                f"{organizations_to_sync}",
            )

        for organization_id in organizations_to_sync:
            credly_api = CredlyAPIClient(organization_id)
            processed_items = credly_api.sync_organization_badge_templates(site_id)

            logger.info(f"Organization {organization_id}: got {processed_items} badge templates.")

        logger.info("...completed!")
