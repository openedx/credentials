import textwrap
from unittest import mock

import ddt
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from slugify import slugify
from testfixtures import LogCapture

from credentials.apps.catalog.data import ProgramStatus
from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.models import ProgramCompletionEmailConfiguration
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory
from credentials.apps.credentials.utils import send_program_certificate_created_message, validate_duplicate_attributes


User = get_user_model()


@ddt.ddt
class CredentialsUtilsTests(TestCase):
    """Tests for credentials.utils methods"""

    def test_with_non_duplicate_attributes(self):
        """Verify that the function will return True if no duplicated attributes found."""
        attributes = [
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
            {"name": "grade", "value": "0.85"},
        ]
        self.assertTrue(validate_duplicate_attributes(attributes))

    def test_with_duplicate_attributes(self):
        """Verify that the function will return False if duplicated attributes found."""

        attributes = [
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
        ]

        self.assertFalse(validate_duplicate_attributes(attributes))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProgramCertificateIssuedEmailTests(SiteMixin, TestCase):
    """
    Tests for the automated email sent to learners after completing an edX Program.

    Testing that the right configuration is used is done in `test_models.py` so this code
    will only verify that an email matching the configuration is sent.
    """

    USERNAME = "test-user"
    FAKE_PROGRAM_UUID = "f6551af4-aa5a-4089-801b-53485d0d1726"

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = None
        self.program_cert = None

        mail.outbox = []

        # Setup program and default email config
        self._setup_program_and_program_cert("Example Program")
        self.default_config = ProgramCompletionEmailConfiguration.objects.create(
            identifier="default",
            html_template="<h1>Default Template</h1>",
            plaintext_template="Default Template",
            enabled=True,
        )

    def _setup_program_and_program_cert(self, program_type):
        self.program = ProgramFactory(site=self.site)
        self.program.type = program_type
        self.program.type_slug = slugify(program_type)
        self.program.save()
        self.program_cert = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)

    def _build_expected_plaintext_email_body(self):
        return [
            "Congratulations on completing the {} {} Program!".format(
                self.program.title,
                self.program.type,
            ),
            "Sincerely,",
            "The {} Team".format(self.site.siteconfiguration.platform_name),
            textwrap.dedent(self.default_config.plaintext_template),
        ]

    def _build_expected_html_email_body(self):
        return [
            "Congratulations on completing the {} {} Program!".format(self.program.title, self.program.type),
            "Sincerely,<br/>The {} Team".format(self.site.siteconfiguration.platform_name),
            self.default_config.html_template,
        ]

    def _assert_email_contents(self):
        """
        Utility function that verifies the contents of the generated email
        """
        expected_plaintext_email_contents = self._build_expected_plaintext_email_body()
        expected_html_email_contents = self._build_expected_html_email_body()

        self.assertEqual(1, len(mail.outbox))

        email = mail.outbox[0]
        plaintext_body = email.body
        html_body = email.alternatives[0][0]

        self.assertEqual(email.to[0], self.user.email)
        self._assert_subject(email.subject)
        self._assert_email_body_contents(plaintext_body, expected_plaintext_email_contents)
        self._assert_email_body_contents(html_body, expected_html_email_contents)

    def _assert_subject(self, email_subject):
        """
        Utility method that verifies the subject text of the automated emails being sent to
        learners.
        """
        expected_subject = "Congratulations for finishing your {} {} Program!".format(
            self.program.title, self.program.type
        )
        self.assertEqual(email_subject, expected_subject)

    def _assert_email_body_contents(self, email_body, fragments):
        """
        Utility method that verifies the content in the generated email is as expected.
        """
        for fragment in fragments:
            self.assertIn(fragment, email_body)

    def test_base_template(self):
        send_program_certificate_created_message(self.user.username, self.program_cert, lms_user_id=123)
        self._assert_email_contents()

    def test_no_config(self):
        """With the config deleted, it shouldn't send an email"""
        self.default_config.delete()
        send_program_certificate_created_message(self.user.username, self.program_cert, lms_user_id=123)
        self.assertEqual(0, len(mail.outbox))

    def test_disabled_config(self):
        """With the config disabled, it shouldn't send an email"""
        self.default_config.enabled = False
        self.default_config.save()
        send_program_certificate_created_message(self.user.username, self.program_cert, lms_user_id=123)
        self.assertEqual(0, len(mail.outbox))

    def test_retired_program(self):
        self.program.status = ProgramStatus.RETIRED.value
        self.program.save()
        send_program_certificate_created_message(self.user.username, self.program_cert, lms_user_id=123)
        self.assertEqual(0, len(mail.outbox))

    def test_send_email_exception_occurs(self):
        self._setup_program_and_program_cert("Radical Program")

        expected_messages = [
            "Sending Program completion email to learner with id [{}] in Program [{}]".format(
                self.user.id, self.program.uuid
            ),
            "Unable to send email to learner with id: [{}] for Program [{}]. Error occurred while attempting to "
            "format or send message: Error!".format(self.user.id, self.program.uuid),
        ]

        with LogCapture() as log:
            with mock.patch("edx_ace.ace.send", side_effect=Exception("Error!")):
                send_program_certificate_created_message(self.user.username, self.program_cert, lms_user_id=123)

        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()
