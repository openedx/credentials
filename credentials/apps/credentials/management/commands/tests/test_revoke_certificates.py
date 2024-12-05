"""
Tests for the revoke_certificates management command
"""

from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.management.commands.revoke_certificates import Command
from credentials.apps.credentials.models import RevokeCertificatesConfig, UserCredential
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)


class RevokeCertificatesTests(SiteMixin, TestCase):
    def setUp(self):
        """
        Create several users with multiple UserCredentials in order to verify
        bulk operations.
        """
        super().setUp()
        self.users = UserFactory.create_batch(3)

        # Set up org, courses, and certificate configs
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="coursecertificate"
        )
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )

        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.course_certs = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]

        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.program_cert = ProgramCertificateFactory.create(program_uuid=self.program.uuid, site=self.site)

        # Set up course and program UserCredentials for each test user
        for user in self.users:
            UserCredentialFactory.create(
                username=user.username,
                credential_content_type=self.program_credential_content_type,
                credential=self.program_cert,
            )
            for course_cert in self.course_certs:
                UserCredentialFactory.create(
                    username=user.username,
                    credential_content_type=self.course_credential_content_type,
                    credential=course_cert,
                )

    def test_default_behavior_deletes_progam_certs(self):
        """verify default behavior revokes expected and ONLY expected program certificates"""
        # pick a subset of users to revoke
        users_to_revoke = self.users[:2]

        call_command(
            Command(),
            "--lms_user_ids",
            users_to_revoke[0].lms_user_id,
            users_to_revoke[1].lms_user_id,
            f"--credential_id={self.program_cert.id}",
        )

        revoked_creds = list(UserCredential.objects.filter(status=UserCredential.REVOKED))
        expected_revoked_creds = list(
            UserCredential.objects.filter(
                username__in=[u.username for u in users_to_revoke],
                credential_content_type__model="programcertificate",
            )
        )

        self.assertListEqual(expected_revoked_creds, revoked_creds)

    def test_credential_type_specify(self):
        """verify credential type can be specified"""
        # pick a subset of users to revoke
        users_to_revoke = self.users[:2]
        cred_type_to_revoke = "coursecertificate"
        cred_to_revoke = self.course_certs[0]

        call_command(
            Command(),
            "--lms_user_ids",
            users_to_revoke[0].lms_user_id,
            users_to_revoke[1].lms_user_id,
            f"--credential_id={cred_to_revoke.id}",
            f"--credential_type={cred_type_to_revoke}",
        )

        revoked_creds = list(UserCredential.objects.filter(status=UserCredential.REVOKED))
        expected_revoked_creds = list(
            UserCredential.objects.filter(
                username__in=[u.username for u in users_to_revoke],
                credential_content_type__model=cred_type_to_revoke,
                credential_id=cred_to_revoke.id,
            )
        )
        self.assertListEqual(expected_revoked_creds, revoked_creds)

    def test_dry_run(self):
        """verify dry_run makes no changes"""
        # pick a subset of users to revoke
        users_to_revoke = self.users[:2]

        call_command(
            Command(),
            "--lms_user_ids",
            users_to_revoke[0].lms_user_id,
            users_to_revoke[1].lms_user_id,
            f"--credential_id={self.program_cert.id}",
            "--dry-run",
        )

        revoked_creds = list(UserCredential.objects.filter(status=UserCredential.REVOKED))

        self.assertFalse(revoked_creds)

    def test_verbosity_enabled(self):
        """verify the verbose flag works when enabled"""
        # pick a subset of users to revoke
        users_to_revoke = self.users[:2]
        expected_substring = "Revoking UserCredential"

        with self.assertLogs(level="INFO") as cm:
            call_command(
                Command(),
                "--lms_user_ids",
                users_to_revoke[0].lms_user_id,
                users_to_revoke[1].lms_user_id,
                f"--credential_id={self.program_cert.id}",
                "--verbose",
            )
        self.assertTrue(any(expected_substring in s for s in cm.output))

    def test_verbosity_disabled(self):
        """verify the verbose flag's absence works as expected"""
        # pick a subset of users to revoke
        users_to_revoke = self.users[:2]
        expected_substring = "Revoking UserCredential"

        with self.assertLogs(level="INFO") as cm:
            call_command(
                Command(),
                "--lms_user_ids",
                users_to_revoke[0].lms_user_id,
                users_to_revoke[1].lms_user_id,
                f"--credential_id={self.program_cert.id}",
            )
        self.assertFalse(any(expected_substring in s for s in cm.output))

    def test_invalid_users(self):
        """verify that the inclusion of invalid user IDs results in a warning"""
        # pick a subset of users to revoke
        users_to_revoke = self.users[:2]
        expected_substring = "The following user IDs don't match existing users"

        with self.assertLogs(level="WARNING") as cm:
            call_command(
                Command(),
                "--lms_user_ids",
                users_to_revoke[0].lms_user_id,
                users_to_revoke[1].lms_user_id,
                8675309,
                f"--credential_id={self.program_cert.id}",
                "--verbose",
            )
        self.assertTrue(any(expected_substring in s for s in cm.output))

    def test_validation(self):
        """Test that the input validators are correct"""
        # fake user
        expected = "None of the given lms_user_ids maps to a real user*"
        with self.assertRaisesRegex(CommandError, expected):
            call_command(Command(), "--lms_user_ids", "8675309", "--credential_id", "123")

        # real user, doesn't mapped to a real credential
        expected = "No active certificates match the given criteria"
        with self.assertRaisesRegex(CommandError, expected):
            call_command(Command(), "--lms_user_ids", self.users[0].lms_user_id, "--credential_id", "123")

        # missing credential_id
        expected = "You must specify a credential_id"
        with self.assertRaisesRegex(CommandError, expected):
            call_command(Command(), "--lms_user_ids", self.users[0].lms_user_id)

        # missing lms_user_ids
        expected = "You must specify list of lms_user_ids"
        with self.assertRaisesRegex(CommandError, expected):
            call_command(Command(), "--credential_id", "123")

    def test_args_from_database(self):
        """Correctly parse args from database at the correct times"""
        # Nothing in the database, should default to disabled
        with self.assertRaisesRegex(CommandError, "RevokeCertificatesConfig is disabled.*"):
            call_command(Command(), "--lms_user_ids", "8675309", "--credential_id", "123", "--args-from-database")

        # Add a config
        config = RevokeCertificatesConfig.current()
        config.arguments = f"--lms_user_ids {self.users[0].lms_user_id} --credential_id 90210"
        config.enabled = True
        config.save()

        # Not told to use config, should ignore it
        with self.assertRaisesRegex(CommandError, "None of the given lms_user_ids maps to a real user*"):
            call_command(Command(), "--lms_user_ids", "8675309", "--credential_id", "123")

        # Told to use it, and enabled. Should use config in preference of command line
        with self.assertRaisesRegex(CommandError, "No active certificates match the given criteria"):
            call_command(Command(), "--lms_user_ids", "8675309", "--credential_id", "123", "--args-from-database")

        config.enabled = False
        config.save()

        # Explicitly disabled
        with self.assertRaisesRegex(CommandError, "RevokeCertificatesConfig is disabled.*"):
            call_command(Command(), "--lms_user_ids", "8675309", "--credential_id", "123", "--args-from-database")
