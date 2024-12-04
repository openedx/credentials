"""Management command to revoke certificates given a certificate ID and a list of users"""

import logging
import shlex
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from credentials.apps.credentials.models import RevokeCertificatesConfig, UserCredential


if TYPE_CHECKING:
    from argparse import ArgumentParser

    from django.db.models import QuerySet


logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Management command to revoke certificates.

    Given a certificate ID and a list of users, revoke that certificate ID
    for those users.

    Example usage:

    $ ./manage.py revoke_certificates --lms_user_ids 867 5309 925
    """

    help = "Revoke certificates for a list of LMS user IDs.  Defaults to program certificates."

    def add_arguments(self, parser: "ArgumentParser"):
        """Arguments for the command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Just show a preview of what would happen.",
        )
        parser.add_argument(
            "--args-from-database",
            action="store_true",
            help="Use arguments from the RevokeCertificates model instead of the command line.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="log each update",
        )
        parser.add_argument(
            "--lms_user_ids",
            default=None,
            required=True,
            nargs="+",
            help="Users for whom this certificate should be revoked",
        )
        parser.add_argument(
            "--credential_id",
            default=None,
            required=True,
            help="ID of the certificate to be revoked",
        )
        parser.add_argument(
            "--credential_type",
            default="programcertificate",
            choices=["coursecertificate", "programcertificate", "credlybadgetemplate"],
            help="Type of credential to revoke. Defaults to 'programcertificate'",
        )

    def get_usernames_from_lms_user_ids(self, lms_user_ids: list[str]) -> "QuerySet":
        """
        Generate Users from a list of usernames from a list of user IDs

        Because a UserCredential stores a username, not a foreign key, it's most
        efficient to convert the list of user IDs to users directly, before
        starting the query. Returning a QuerySet of the User objects (instead of
        usernames) allows us to do verbose logging and error reporting.

        Arguments:

            lms_user_ids: list(str):  a list of LMS user IDs

        Returns:

            a QuerySet of User objects.
        """
        users = User.objects.filter(lms_user_id__in=lms_user_ids)
        missing_users = set(lms_user_ids).difference({str(i.lms_user_id) for i in users})
        if missing_users:
            logger.warning(f"The following user IDs don't match existing users: {missing_users}")
        return users

    def get_args_from_database(self):
        """Returns an options dictionary from the current NotifyCredentialsConfig model."""
        config = RevokeCertificatesConfig.current()
        if not config.enabled:
            raise CommandError("RevokeCertificatesConfig is disabled, but --args-from-database was requested.")

        argv = shlex.split(config.arguments)
        parser = self.create_parser("manage.py", "revoke_certificates")
        return parser.parse_args(argv).__dict__  # we want a dictionary, not a non-iterable Namespace object

    def handle(self, *args, **options):
        if options["args_from_database"]:
            options = self.get_args_from_database()
        credential_id = options.get("credential_id")
        verbosity = options.get("verbose")
        credential_type = options.get("credential_type")
        dry_run = options.get("dry_run")
        lms_user_ids = options.get("lms_user_ids")

        logger.info(
            f"revoke_certificates starting, dry-run={dry_run}, credential_id={credential_id}, "
            f"credential_type={credential_type}, lms_user_ids={lms_user_ids}, verbosity={verbosity}"
        )

        if not lms_user_ids:
            raise CommandError("You must specify list of lms_user_ids")
        users = self.get_usernames_from_lms_user_ids(lms_user_ids)
        if not users:
            raise CommandError("None of the given lms_user_ids maps to a real user")

        # We use usernames here, not foreign keys, so just make a list.
        # This is not going to be a huge set of users, run from a management command.
        usernames = [i.username for i in users]  # type: list[str]

        user_creds_to_revoke = UserCredential.objects.filter(
            username__in=usernames,
            status=UserCredential.AWARDED,
            credential_content_type__model=credential_type,
            credential_id=credential_id,
        )
        if not user_creds_to_revoke:
            raise CommandError("No active certificates match the given criteria")

        # as a manually input list, this should be small enough to do in a single bulk_update
        for user_cred in user_creds_to_revoke:
            if verbosity:
                # It's not worth doing an extra query to annotate the verbose logging message with
                # user ID, and username isn't PII safe. If the person reading the logs wants more
                # info about the affected users, this log message includes enough to look them up.
                logger.info(f"Revoking UserCredential {user_cred.id} ({credential_type} {credential_id})")
            user_cred.status = UserCredential.REVOKED
        if not dry_run:
            user_creds_to_revoke.bulk_update(user_creds_to_revoke, ["status"])

        logger.info("Done revoking certificates")
