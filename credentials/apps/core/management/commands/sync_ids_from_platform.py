"""
Django managment command to sync missing lms user ids from platform
"""

import logging
import time
from urllib.parse import urljoin
from urllib.error import HTTPError

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from credentials.apps.core.models import SiteConfiguration

User = get_user_model()
logger = logging.getLogger(__name__)

site_configs = SiteConfiguration.objects.first()

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch_size", 
            type=int, 
            default=10, 
            help="Number of IDs to process at a time. Default 10")
        parser.add_argument(
            "--pause_ms", 
            type=int, 
            default=1, 
            help="Number of seconds to pause between calls. Default 1 sec")
        parser.add_argument(
            "--limit", 
            type=int, 
            default=0, 
            help="Total number of IDs to update. 0 for update all, Default is 0 (all)")

    def handle(self, *args, **options):
        """
            Get batches of user info from accounts and update the lms_user_id
            for users who are missing it.
        """
        users_without_lms_id = User.objects.filter(lms_user_id=None)
        num_users_to_update = users_without_lms_id.count()
        offset = options.get("batch_size")
        pause = options.get("pause_ms")
        count = options.get("limit")
        # Get the actual number of users to process, an arg of 0 means all of them
        count = min(count, num_users_to_update)
        if (0 == count):
            count = num_users_to_update
               
        if count == 0:
            logger.warn("No users to update. Stopping")
            return

        logger.warn(f"Start processing {count} IDs with no lms_user_id")

        # loop over users in batches    
        for x in range(0, count, offset):
            # don't go past the end of the loop
            slice_size = min(count, x+offset)
            curr_users = users_without_lms_id[x: slice_size]
            ids = self.get_lms_ids(curr_users)
            for user in curr_users:
                try:
                    self.update_user(user, ids[user.username])
                except:
                    logger.error(f"Could not update lms_user_id for user {user.username}")
            if x + slice_size < count:
                time.sleep(pause)
        else:
            logger.warn("sync_ids_from_platform finished!")
        

    def get_lms_ids(self, users):
        """
        given a list of users, query platform and get lms_user_ids
        return a dict of lms_user_ids keyed by username
        """
        user_dict = dict()
        # create a comma separated string with the usernames
        user_name_list = ','.join(user.username for user in users)
        user_url = urljoin(site_configs.user_api_url, f"accounts?username={user_name_list}")
        try:
            user_response = site_configs.api_client.get(user_url)
            user_response.raise_for_status()
            user_data = user_response.json()

            for user_profile in user_data:
                user_dict[user_profile["username"]] = user_profile["id"]
        except HTTPError as http_error:
            logger.error(f"An HTTP error occurred {http_error}")

        return user_dict    

    def update_user(self, user, id):
        """ update the lms_user_id for the user """
        if id and id > 0:
            user.lms_user_id = id
            user.save(update_fields=['lms_user_id'])




