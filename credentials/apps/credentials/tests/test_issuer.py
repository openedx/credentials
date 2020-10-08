"""
Tests for Issuer class.
"""
from unittest import mock

from django.test import TestCase, override_settings

from credentials.apps.api.exceptions import DuplicateAttributeError
from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.credentials.issuers import CourseCertificateIssuer, ProgramCertificateIssuer
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    UserCredential,
    UserCredentialAttribute,
)
from credentials.apps.credentials.tests.factories import CourseCertificateFactory, ProgramCertificateFactory


LOGGER_NAME = 'credentials.apps.credentials.issuers'


# pylint: disable=no-member
class CertificateIssuerBase:
    """ Tests an Issuer class and its methods."""
    issuer = None
    cert_factory = None
    cert_type = None

    def setUp(self):
        super().setUp()
        self.certificate = self.cert_factory.create()
        self.username = 'tester'
        self.user = UserFactory(username=self.username)
        self.user_cred = self.issuer.issue_credential(self.certificate, self.username)
        self.attributes = [{"name": "whitelist_reason", "value": "Reason for whitelisting."}]

    def test_issued_credential_type(self):
        """ Verify issued_credential_type returns the correct credential type."""
        self.assertEqual(self.issuer.issued_credential_type, self.cert_type)

    def test_issue_existing_credential(self):
        """ Verify credentials can be updated when re-issued."""

        user_credential = self.issuer.issue_credential(self.certificate, self.username, 'revoked')
        self.user_cred.refresh_from_db()
        self._assert_usercredential_fields(self.user_cred, self.certificate, self.username, 'revoked', [])
        self.assertEqual(user_credential, self.user_cred)

    def test_issue_credential_without_attributes(self):
        """ Verify credentials can be issued without attributes."""

        user_credential = self.issuer.issue_credential(self.certificate, self.username)
        self._assert_usercredential_fields(user_credential, self.certificate, self.username, 'awarded', [])

    def test_issue_credential_with_attributes(self):
        """ Verify credentials can be issued with attributes."""
        UserFactory(username='testuser2')
        user_credential = self.issuer.issue_credential(self.certificate, 'testuser2', attributes=self.attributes)
        self._assert_usercredential_fields(user_credential, self.certificate, 'testuser2', 'awarded', self.attributes)

    def _assert_usercredential_fields(self, user_credential, expected_credential, expected_username, expected_status,
                                      expected_attrs):
        """ Verify the fields on a UserCredential object match expectations. """
        self.assertEqual(user_credential.username, expected_username)
        self.assertEqual(user_credential.credential, expected_credential)
        self.assertEqual(user_credential.status, expected_status)
        actual_attributes = [{'name': attr.name, 'value': attr.value} for attr in user_credential.attributes.all()]
        self.assertEqual(actual_attributes, expected_attrs)

    def test_set_credential_without_attributes(self):
        """ Verify that if no attributes given then None will return."""
        self.assertEqual(
            self.issuer.set_credential_attributes(self.user_cred, None),
            None
        )

    def test_set_credential_with_attributes(self):
        """ Verify that it adds the given attributes against user credential."""

        self.issuer.set_credential_attributes(self.user_cred, self.attributes)
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, 'awarded', self.attributes
        )

    def test_set_credential_with_duplicate_attributes_by_util(self):
        """Verify in case of duplicate attributes utils method will return False and
        exception will be raised.
        """

        self.attributes.append({"name": "whitelist_reason", "value": "Reason for whitelisting."})

        with self.assertRaises(DuplicateAttributeError):
            self.issuer.set_credential_attributes(self.user_cred, self.attributes)

    def test_existing_credential_with_duplicate_attributes(self):
        """Verify if user credential attributes already exists in db then method will
        update existing attributes values."""

        # add the attribute in db and then try to create the credential
        # with same data "names but value is different"

        attribute_db = {"name": "whitelist_reason", "value": "Reason for whitelisting."}

        UserCredentialAttribute.objects.create(
            user_credential=self.user_cred,
            name=attribute_db.get("name"),
            value=attribute_db.get("value")
        )
        self.issuer.set_credential_attributes(self.user_cred, self.attributes)

        # first attribute value will be changed to 0.5
        self._assert_usercredential_fields(
            self.user_cred,
            self.certificate,
            self.user_cred.username,
            'awarded',
            self.attributes
        )

    def test_existing_attributes_with_empty_attributes_list(self):
        """Verify if user credential attributes already exists in db then in case of empty
        attributes list it will return without changing any data."""

        self.issuer.set_credential_attributes(self.user_cred, self.attributes)
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, 'awarded', self.attributes
        )

        # create same credential without attributes.
        self.assertIsNone(self.issuer.set_credential_attributes(self.user_cred, []))
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, 'awarded', self.attributes
        )


class ProgramCertificateIssuerTests(CertificateIssuerBase, TestCase):
    """ Tests for program Issuer class and its methods."""
    issuer = ProgramCertificateIssuer()
    cert_factory = ProgramCertificateFactory
    cert_type = ProgramCertificate

    def setUp(self):
        super().setUp()
        self.site = SiteFactory()
        self.site_config = SiteConfigurationFactory(site=self.site)
        self.program = ProgramFactory(site=self.site)
        self.certificate = self.cert_factory.create(program_uuid=self.program.uuid, site=self.site)
        self.username = 'tester2'
        self.user = UserFactory(username=self.username)
        self.user_cred = self.issuer.issue_credential(self.certificate, self.username)
        self.attributes = [{"name": "whitelist_reason", "value": "Reason for whitelisting."}]

    def test_records_enabled_is_unchecked(self):
        """Verify that if SiteConfiguration.records_enabled is unchecked then don't send
        updated email to a pathway org.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        with mock.patch('credentials.apps.credentials.issuers.send_updated_emails_for_program') as mock_method:
            self.issuer.issue_credential(self.certificate, 'testuser3', attributes=self.attributes)
            self.assertEqual(mock_method.call_count, 0)

    def test_records_enabled_is_checked(self):
        """Verify that if SiteConfiguration.records_enabled is checked and new record is created
        then updated email is sent to a pathway org.
        """
        with mock.patch('credentials.apps.credentials.issuers.send_updated_emails_for_program') as mock_method:
            self.issuer.issue_credential(self.certificate, 'testuser4', attributes=self.attributes)
            self.assertEqual(mock_method.call_count, 1)

    @override_settings(SEND_EMAIL_ON_PROGRAM_COMPLETION=True)
    @mock.patch('credentials.apps.credentials.issuers.send_program_certificate_created_message')
    def test_send_learner_email_when_issuing_program_cert(self, mock_send_learner_email):
        self.site_config.records_enabled = False
        self.site_config.save()

        self.issuer.issue_credential(self.certificate, 'testuser5')
        self.assertEqual(mock_send_learner_email.call_count, 1)

    @override_settings(SEND_EMAIL_ON_PROGRAM_COMPLETION=True)
    @mock.patch('credentials.apps.credentials.issuers.send_program_certificate_created_message')
    def test_send_learner_email_only_once(self, mock_send_learner_email):
        """
        Verify that we call `send_program_certificate_created_message` only once if a
        certificate already exists and is being awarded again after being revoked.
        """
        username = 'learner'
        user = UserFactory(username=username)

        self.site_config.records_enabled = False
        self.site_config.save()

        self.issuer.issue_credential(self.certificate, user.username)
        # revoke the user credential
        user_credential = UserCredential.objects.get(username=username)
        user_credential.revoke()
        # issue the credential again, make sure that we haven't tried to send the email again
        self.issuer.issue_credential(self.certificate, user.username)
        self.assertEqual(mock_send_learner_email.call_count, 1)

    @override_settings(SEND_EMAIL_ON_PROGRAM_COMPLETION=False)
    @mock.patch('credentials.apps.credentials.issuers.send_program_certificate_created_message')
    def test_do_not_send_learner_email_when_feature_disabled(self, mock_send_learner_email):
        """
        Verify that we do NOT try to send an email to the learner when a Program Cert is issued
        if the feature is disabled.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        self.issuer.issue_credential(self.certificate, 'testuser6')
        self.assertEqual(mock_send_learner_email.call_count, 0)


class CourseCertificateIssuerTests(CertificateIssuerBase, TestCase):
    """ Tests for course Issuer class and its methods."""
    issuer = CourseCertificateIssuer()
    cert_factory = CourseCertificateFactory
    cert_type = CourseCertificate
