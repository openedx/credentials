"""
Django management command to make the is_active status on a credentials user
be True if the user's LMS is_active status is True.

If the credentials user is_active=True but the LMS user is_active=False, we don't need to synchronize because that
inconsistency is fine. But there can be user problems if they can log in to the
LMS but the credentials user has been set inactive, so we have to fix inconsistencies in
that one direction.
"""

import logging
import time
from typing import TYPE_CHECKING, Dict, List
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from credentials.apps.core.models import SiteConfiguration


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--batch_size", type=int, default=10, help="Number of IDs to process at a time. Default %(default)"
        )
        parser.add_argument(
            "--pause_secs", type=int, default=1, help="Number of seconds to pause between calls. Default %(default)"
        )
        parser.add_argument("--verbose", action="store_true", help="Log each update")
        parser.add_argument(
            "--site_id", type=int, default=0, help="ORM id of the site to query for lms_user_ids. Default %(default)"
        )
        parser.add_argument("--dry_run", action="store_true", help="Don't actually change the data")

    def handle(self, *args, **options):
        """
        Get batches of user info from accounts and update the lms_user_id
        for users who are missing it.
        """
        logger.info("Beginning is_active matching.")
        inactive_credentials_users = User.objects.filter(is_active=False)
        count_users = inactive_credentials_users.count()
        offset = options.get("batch_size")
        pause = options.get("pause_secs")
        verbosity = options.get("verbose")
        site_id = options.get("site_id")
        dry_run = options.get("dry_run")

        site_configs = SiteConfiguration.objects.first()
        if site_id:
            # multiple are sites managing different users
            logger.info(f"using site id {site_id} for user queries")
            site_configs = SiteConfiguration.objects.get(site__id=site_id)
        logger.info(f"using {site_configs.site.domain} for user queries")

        # loop over users in batches
        logger.warning(f"Start processing {count_users} inactive Credentials user accounts")
        for x in range(0, count_users, offset):
            slice_size = min(count_users, x + offset)
            curr_users = inactive_credentials_users[x:slice_size]
            is_active_statuses = self.get_is_active(curr_users, site_configs)
            for user in curr_users:
                if user.username not in is_active_statuses:
                    logger.error(f"Could not get is_active for user with lms_user_id {user.lms_user_id}")
                elif user.is_active != is_active_statuses[user.username]:
                    self.enable_user(user, verbosity, dry_run)
            if x + slice_size < count_users:
                time.sleep(pause)

        logger.info("Finished is_active matching.")

    def get_is_active(
        self,
        users: List["AbstractUser"],
        site_config: SiteConfiguration,
    ) -> Dict[str, bool]:
        """Get is_active status from the LMS for a list of users.

        Args:
            users: List of user objects
            site_config: SiteConfiguration object of Site to query

        Returns:
            a dict of form { username[str]: is_active[bool] }
        """
        query_param_names = ",".join(user.username for user in users)
        user_url = urljoin(site_config.user_api_url, f"accounts?username={query_param_names}")
        user_response = site_config.api_client.get(user_url)

        user_dict = {}
        if user_response.status_code == 200:
            user_data = user_response.json()
            for user_profile in user_data:
                user_dict[user_profile["username"]] = user_profile["is_active"]
        else:
            logger.error(
                f"{urljoin(site_config.user_api_url, 'accounts?username=')}[usernames redacted]"
                f"returned status {user_response.status_code}"
            )

        return user_dict

    def enable_user(self, user: "AbstractUser", verbosity: bool, dry_run: bool) -> None:
        """Update the is_active status for the user.

        Although this management command is written to only update from False to True,

        """
        user.is_active = True
        dry_run_msg = "(dry run) " if dry_run else ""
        if verbosity:
            logger.info(f"{dry_run_msg}Setting user with lms_user_id {user.lms_user_id} to active status")
        # use update_fields to just update this one piece of data
        if not dry_run:
            user.save(update_fields=["is_active"])
