from django.core.management.base import BaseCommand

from credentials.apps.badges.accredible.api_client import AccredibleAPIClient
from credentials.apps.badges.models import AccredibleAPIConfig


class Command(BaseCommand):
    """
    Sync groups for a specific accredible api config or all configs.

    Usage:
        site_id=1
        api_config_id=1

        ./manage.py sync_accredible_groups --site_id $site_id
        ./manage.py sync_accredible_groups --site_id $site_id --api_config_id $api_config_id
    """

    help = "Sync accredible groups for a specific api config or all api configs"

    def add_arguments(self, parser):
        parser.add_argument("--site_id", type=int, help="Site ID.")
        parser.add_argument("--api_config_id", type=str, help="ID of the API config.")

    def handle(self, *args, **options):
        """
        Handle the command.
        """
        DEFAULT_SITE_ID = 1
        api_configs_to_sync = []

        site_id = options.get("site_id")
        api_config_id = options.get("api_config_id")

        if site_id is None:
            self.stdout.write(f"Site ID wasn't provided: assuming site_id = {DEFAULT_SITE_ID}")
            site_id = DEFAULT_SITE_ID

        if api_config_id:
            api_configs_to_sync.append(api_config_id)
            self.stdout.write(f"Syncing groups for the single config: {api_config_id}")
        else:
            api_configs_to_sync = AccredibleAPIConfig.get_all_api_config_ids()
            self.stdout.write(
                "API Config ID wasn't provided: syncing groups for all configs - " f"{api_configs_to_sync}",
            )

        for api_config in AccredibleAPIConfig.objects.filter(id__in=api_configs_to_sync):
            accredible_api_client = AccredibleAPIClient(api_config.id)
            processed_items = accredible_api_client.sync_groups(site_id)

            self.stdout.write(f"API Config {api_config_id}: got {processed_items} groups.")

        self.stdout.write("...completed!")
