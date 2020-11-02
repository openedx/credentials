import datetime
import textwrap
from unittest import mock

import ddt
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from slugify import slugify
from testfixtures import LogCapture

from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory
from credentials.apps.credentials.utils import (
    datetime_from_visible_date,
    send_program_certificate_created_message,
    validate_duplicate_attributes,
)


User = get_user_model()


@ddt.ddt
class CredentialsUtilsTests(TestCase):
    """ Tests for credentials.utils methods """

    def test_with_non_duplicate_attributes(self):
        """ Verify that the function will return True if no duplicated attributes found."""
        attributes = [
            {'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'},
            {'name': 'grade', 'value': '0.85'}
        ]
        self.assertTrue(validate_duplicate_attributes(attributes))

    def test_with_duplicate_attributes(self):
        """ Verify that the function will return False if duplicated attributes found."""

        attributes = [
            {'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'},
            {'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'},
        ]

        self.assertFalse(validate_duplicate_attributes(attributes))

    def test_datetime_from_visible_date(self):
        """ Verify that we convert LMS dates correctly. """
        self.assertIsNone(datetime_from_visible_date(''))
        self.assertIsNone(datetime_from_visible_date('2018-07-31'))
        self.assertIsNone(datetime_from_visible_date('2018-07-31T09:32:46+00:00'))  # should be Z for timezone
        self.assertEqual(datetime_from_visible_date('2018-07-31T09:32:46Z'),
                         datetime.datetime(2018, 7, 31, 9, 32, 46, tzinfo=datetime.timezone.utc))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProgramCertificateIssuedEmailTests(SiteMixin, TestCase):
    """
    Tests for the automated email sent to learners after completing an edX Program.
    """
    USERNAME = "test-user"
    FAKE_PROGRAM_UUID = 'f6551af4-aa5a-4089-801b-53485d0d1726'

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = None
        self.program_cert = None

        mail.outbox = []

    def _get_custom_completion_email_template_settings(self):
        return {
            'f6551af4-aa5a-4089-801b-53485d0d1726': {
                'plaintext': '''
                I am email one
                I have the best content
                ''',
                'html': '''
                <p>I am email one</p>
                <p>I have the best content</p>
                ''',
            },
            'excellent-program': {
                'plaintext': '''
                I am email two
                I have better content
                ''',
                'html': '''
                <p>I am email two</p>
                <p>I have better content</p>
                ''',
            },
            'tubular-program': {
                'plaintext': '''
                I am email three
                I have great content too
                ''',
                'html': '''
                <p>I am email three</p>
                <p>I have great content too</p>
                ''',
            }
        }

    def _setup_program_and_program_cert(self, program_type, uuid=None):
        self.program = ProgramFactory(site=self.site)
        self.program.type = program_type
        self.program.type_slug = slugify(program_type)

        if uuid:
            self.program.uuid = uuid

        self.program.save()

        self.program_cert = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)

    def _build_expected_plaintext_email_body(self):
        custom_completion_email_template_settings = self._get_custom_completion_email_template_settings()

        email_fragments = [
            'Congratulations on completing the {} {} Program!'.format(
                self.program.title,
                self.program.type,
            ),
            'Sincerely,',
            'The {} Team'.format(
                self.site.siteconfiguration.platform_name
            ),
        ]

        if custom_completion_email_template_settings.get(self.program.uuid):
            email_fragments.append(textwrap.dedent(
                custom_completion_email_template_settings.get(self.program.uuid).get('plaintext')))
        elif custom_completion_email_template_settings.get(self.program.type_slug):
            email_fragments.append(textwrap.dedent(
                custom_completion_email_template_settings.get(self.program.type_slug).get('plaintext')))

        return email_fragments

    def _build_expected_html_email_body(self):
        custom_completion_email_template_settings = self._get_custom_completion_email_template_settings()

        email_fragments = [
            "Congratulations on completing the {} {} Program!".format(
                self.program.title,
                self.program.type
            ),
            'Sincerely,<br/>The {} Team'.format(
                self.site.siteconfiguration.platform_name
            ),
        ]

        if custom_completion_email_template_settings.get(self.program.uuid):
            email_fragments.append(custom_completion_email_template_settings.get(self.program.uuid).get('html'))
        elif custom_completion_email_template_settings.get(self.program.type_slug):
            email_fragments.append(custom_completion_email_template_settings.get(self.program.type_slug).get('html'))

        return email_fragments

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
        expected_subject = 'Congratulations for finishing your {} {} Program!'.format(
            self.program.title,
            self.program.type
        )
        self.assertEqual(email_subject, expected_subject)

    def _assert_email_body_contents(self, email_body, fragments):
        """
        Utility method that verifies the content in the generated email is as expected.
        """
        for fragment in fragments:
            self.assertIn(fragment, email_body)

    def test_base_template(self):
        self._setup_program_and_program_cert('Radical Program')

        send_program_certificate_created_message(self.user.username, self.program_cert)

        self._assert_email_contents()

    def test_custom_email_template_program_uuid(self):
        """
        Test for the contents of a custom email template.
        """
        self._setup_program_and_program_cert('Excellent Program', self.FAKE_PROGRAM_UUID)

        with self.settings(
            CUSTOM_COMPLETION_EMAIL_TEMPLATE_EXTRA=self._get_custom_completion_email_template_settings()
        ):
            send_program_certificate_created_message(self.user.username, self.program_cert)

        self._assert_email_contents()

    def test_custom_email_template_program_type(self):
        self._setup_program_and_program_cert('Excellent Program')

        with self.settings(
            CUSTOM_COMPLETION_EMAIL_TEMPLATE_EXTRA=self._get_custom_completion_email_template_settings()
        ):
            send_program_certificate_created_message(self.user.username, self.program_cert)

        self._assert_email_contents()

    def test_custom_email_template_alternative_program_type(self):
        self._setup_program_and_program_cert('Tubular Program')

        with self.settings(
            CUSTOM_COMPLETION_EMAIL_TEMPLATE_EXTRA=self._get_custom_completion_email_template_settings()
        ):
            send_program_certificate_created_message(self.user.username, self.program_cert)

        self._assert_email_contents()

    def test_send_email_exception_occurs(self):
        self._setup_program_and_program_cert("Radical Program")

        expected_messages = [
            'Sending Program completion email to learner with id [{}] in Program [{}]'.format(
                self.user.id,
                self.program.uuid
            ),
            'Unable to send email to learner with id: [{}] for Program [{}]. Error occurred while attempting to '
            'format or send message: Error!'.format(
                self.user.id,
                self.program.uuid
            )
        ]

        with LogCapture() as log:
            with mock.patch('edx_ace.ace.send', side_effect=Exception("Error!")):
                send_program_certificate_created_message(self.user.username, self.program_cert)

        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()
