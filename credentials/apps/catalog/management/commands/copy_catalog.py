""" Copy catalog data from Discovery. """

import logging

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
            log_results = synchronizer.fetch_data()
            # We have to log them one at a time because we can run into "Message too long" errors
            for line in log_results:
                self.stdout.write(line)
            if delete_data:
                synchronizer.remove_obsolete_data()
