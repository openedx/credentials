"""Copy catalog data from Discovery."""

import logging
import sys

from django.contrib.sites.models import Site
from django.core.management import BaseCommand

from credentials.apps.catalog.utils import CatalogDataSynchronizer
from credentials.apps.core.models import SiteConfiguration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Copy catalog data from Discovery"

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            "--page-size",
            action="store",
            type=int,
            default=None,
            help="The maximum number of catalog items to request at once.",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            dest="delete_data",
            required=False,
            help="Delete catalog data that doesn't exist in Discovery service",
        )

    def handle(self, *args, **options):
        page_size = options.get("page_size")
        delete_data = options.get("delete_data")

        for site in Site.objects.all():
            site_configs = SiteConfiguration.objects.filter(site=site)
            site_config = site_configs.get() if site_configs.exists() else None

            # We skip the site if records_enabled is false - remember to remove that check once we start
            # using the catalog data for certificates too.
            if not site_config or not site_config.catalog_api_url or not site_config.records_enabled:
                logger.info(f"Skipping site {site.domain}. No configuration.")
                continue

            synchronizer = CatalogDataSynchronizer(
                site=site,
                api_client=site_config.api_client,
                catalog_api_url=site_config.catalog_api_url,
                page_size=page_size,
            )
            result_data = synchronizer.fetch_data()

            self.stdout.write("The copy_catalog command caused the following changes:")
            for model, model_changes in result_data.items():
                if model_changes["added"]:
                    self.stdout.write(f"{model} UUIDs added: {model_changes['added']}")
                if model_changes["removed"]:
                    self.stdout.write(f"{model} UUIDs to be removed: {model_changes['removed']}")

            if delete_data:
                self.stdout.write("Deleting obsolete data")
                synchronizer.remove_obsolete_data()
                self.stdout.write("Obsolete data deleted")
            else:
                # If we're not deleting and there is data to be deleted, fail so we can notice, review the deletions,
                # and run again with --delete
                if any((value["removed"] for value in result_data.values())):
                    self.stdout.write(
                        "FAILURE: There is data that needs to be deleted. Please review UUIDs above and re-run with"
                        + " --delete parameter"
                    )
                    sys.exit(1)
