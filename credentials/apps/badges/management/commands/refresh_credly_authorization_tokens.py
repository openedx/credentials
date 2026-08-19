import logging

from django.core.management.base import BaseCommand

from credentials.apps.badges.credly.api_client import CredlyAPIClient
from credentials.apps.badges.exceptions import BadgesError
from credentials.apps.badges.models import CredlyOrganization

logger = logging.getLogger(__name__)

# Start warning operators once a token is within this many days of expiration.
WARNING_THRESHOLD_DAYS = 30
# Automatically rotate a token once fewer than this many days remain.
REFRESH_THRESHOLD_DAYS = 5


class Command(BaseCommand):
    help = (
        "Check Credly authorization tokens and keep them alive: log a warning when a token is "
        f"within {WARNING_THRESHOLD_DAYS} days of expiration and automatically rotate it once fewer "
        f"than {REFRESH_THRESHOLD_DAYS} days remain. Intended to be run periodically (e.g. daily cron)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--organization_id",
            type=str,
            help="UUID of a single Credly organization to check. Defaults to all organizations.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Rotate the token immediately, regardless of the remaining lifetime.",
        )

    def handle(self, *args, **options):
        """
        Refresh Credly authorization tokens that are close to expiration.

        Usage:
            ./manage.py refresh_credly_authorization_tokens
            ./manage.py refresh_credly_authorization_tokens --organization_id <uuid>
            ./manage.py refresh_credly_authorization_tokens --force
        """
        organization_id = options.get("organization_id")
        force = options.get("force")

        if organization_id:
            organizations = CredlyOrganization.objects.filter(uuid=organization_id)
            if not organizations:
                logger.warning(f"No Credly organization found with the uuid {organization_id}.")
        else:
            organizations = CredlyOrganization.objects.all()

        for organization in organizations:
            self._process_organization(organization, force=force)

        logger.info("...completed!")

    def _process_organization(self, organization, force=False):
        """
        Inspect a single organization's token and warn and/or rotate as needed.
        """
        if force:
            logger.info(f"Organization {organization.uuid}: forcing authorization token rotation.")
            self._rotate(organization)
            return

        days_left = organization.authorization_token_days_until_expiry

        if days_left is None:
            logger.warning(
                f"Organization {organization.uuid}: authorization token issuance date is unknown, so its "
                "expiration cannot be determined. Rotate it manually or run this command with --force."
            )
            return

        if days_left < REFRESH_THRESHOLD_DAYS:
            logger.warning(
                f"Organization {organization.uuid}: authorization token expires in {days_left} day(s); "
                "rotating it now."
            )
            self._rotate(organization)
        elif days_left <= WARNING_THRESHOLD_DAYS:
            logger.warning(
                f"Organization {organization.uuid}: authorization token expires in {days_left} day(s). "
                f"It will be rotated automatically once fewer than {REFRESH_THRESHOLD_DAYS} days remain."
            )
        else:
            logger.info(f"Organization {organization.uuid}: authorization token is healthy ({days_left} day(s) left).")

    def _rotate(self, organization):
        """
        Rotate a single organization's authorization token, logging the outcome.
        """
        try:
            CredlyAPIClient(organization.uuid).rotate_authorization_token()
            logger.info(f"Organization {organization.uuid}: authorization token rotated successfully.")
        except BadgesError as exc:
            logger.error(f"Organization {organization.uuid}: failed to rotate authorization token: {exc}")
