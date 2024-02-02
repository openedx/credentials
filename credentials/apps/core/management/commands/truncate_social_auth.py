"""
Django managment command to truncate the social_auth_usersocialauth table.

The social-auth-app-django plugin can have migrations on upgrade, and those
migrations can fail when the social_auth_usersocialauth table is too large.
It's safe to truncate the table; it doesn't affect logged in users at all.
However, to avoid any risk, this keeps a window of learners who have logged
in in the last 90 days.
"""

import logging
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from social_django.models import UserSocialAuth


logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Truncate the social_auth_usersocialauth table."""
        now = datetime.now(timezone.utc)
        error_message = "truncate_social_auth deleted failed"
        # This is unlikely to be a run-more-than-once management command.
        # If the need rearises, this timedelta could become an argument.
        window_to_keep = timedelta(days=90)
        try:
            deleted = UserSocialAuth.objects.filter(modified__lte=now - window_to_keep).delete()
        except:  # pylint: disable=bare-except
            logger.exception(error_message)
        try:
            logger.info(f"truncate_social_auth deleted {deleted[0]} rows")
        except IndexError:
            logger.error(error_message)
