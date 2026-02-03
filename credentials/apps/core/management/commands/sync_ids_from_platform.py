"""
Django managment command to sync missing lms user ids from platform
"""

import logging
import time
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from credentials.apps.core.models import SiteConfiguration

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--batch_size", type=int, default=10, help="Number of IDs to process at a time. Default 10")
        parser.add_argument(
            "--pause_secs", type=int, default=1, help="Number of seconds to pause between calls. Default 1 sec"
        )
        parser.add_argument(
            "--limit", type=int, default=100, help="Total number of IDs to update. 0 for update all, Default is 100"
        )
        parser.add_argument("--verbose", action="store_true", help="Log each update")
        parser.add_argument("--site_id", type=int, default=0, help="ORM id of the site to query for lms_user_ids")
        parser.add_argument("--dry_run", action="store_true", help="Don't actually change the data")

    def handle(self, *args, **options):
        """
        Get batches of user info from accounts and update the lms_user_id
        for users who are missing it.
        """
        users_without_lms_id = User.objects.filter(lms_user_id=None)
        num_users_to_update = users_without_lms_id.count()
        offset = options.get("batch_size")
        pause = options.get("pause_secs")
        limit = options.get("limit")
        verbosity = options.get("verbose")
        site_id = options.get("site_id")
        dry_run = options.get("dry_run")

        site_configs = SiteConfiguration.objects.first()
        # if there are multiple sites managing different users
        # This is likely rare
        if site_id:
            logger.info(f"using site id {site_id} for user queries")
            site_configs = SiteConfiguration.objects.get(site__id=site_id)

        logger.info(f"using {site_configs.site.domain} for user queries")

        # Get the actual number of users to process, an arg of 0 means all of them
        count = min(limit, num_users_to_update)
        if 0 == limit:
            count = num_users_to_update

        logger.warning(f"Start processing {count} IDs with no lms_user_id")

        # loop over users in batches
        for x in range(0, count, offset):
            # don't go past the end of the loop
            slice_size = min(count, x + offset)
            curr_users = users_without_lms_id[x:slice_size]
            ids = self.get_lms_ids(curr_users, site_configs)
            for user in curr_users:
                # did the endpoint return a value for this user?
                if user.username in ids:
                    self.update_user(user, ids[user.username], verbosity, dry_run)
                else:
                    logger.error(f"Could not get lms_user_id for user {user.username}")
            if x + slice_size < count:
                time.sleep(pause)

        logger.warning("sync_ids_from_platform finished!")

    def get_lms_ids(self, users, site_configs):
        """
        given a list of users, query platform and get lms_user_ids
        return a dict of lms_user_ids keyed by username
        """
        user_dict = {}
        # create a comma separated string with the usernames
        query_param_names = ",".join(user.username for user in users)
        user_url = urljoin(site_configs.user_api_url, f"accounts?username={query_param_names}")
        user_response = site_configs.api_client.get(user_url)
        if 200 == user_response.status_code:
            user_data = user_response.json()

            for user_profile in user_data:
                user_dict[user_profile["username"]] = user_profile["id"]
        else:
            logger.error(f" {user_url} returned status {user_response.status_code}")

        return user_dict

    def update_user(self, user, lms_user_id, verbosity, dry_run):
        """update the lms_user_id for the user"""
        if lms_user_id and lms_user_id > 0:
            user.lms_user_id = lms_user_id
            dry_run_msg = "(dry run) " if dry_run else ""
            if verbosity:
                logger.info(f"{dry_run_msg}updating {user.username} with id {lms_user_id}")
            # use update_fields to just update this one piece of data
            if not dry_run:
                user.save(update_fields=["lms_user_id"])
