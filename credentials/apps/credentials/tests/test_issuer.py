"""
Tests for Issuer classes.
"""
from unittest import mock
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from openedx_events.learning.data import ProgramCertificateData, ProgramData, UserData, UserPersonalData
from testfixtures import LogCapture

from credentials.apps.api.exceptions import DuplicateAttributeError
from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.issuers import CourseCertificateIssuer, ProgramCertificateIssuer
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    UserCredential,
    UserCredentialAttribute,
)
from credentials.apps.credentials.tests.factories import CourseCertificateFactory, ProgramCertificateFactory


User = get_user_model()
LOGGER_NAME = "credentials.apps.credentials.issuers"


# pylint: disable=no-member
class CertificateIssuerBase:
    """
    Tests an Issuer class and its methods.
    """

    issuer = None
    cert_factory = None
    cert_type = None

    def setUp(self):
        super().setUp()
        self.certificate = self.cert_factory.create()
        self.username = "tester"
        self.user = UserFactory(username=self.username)
        self.user_cred = self.issuer.issue_credential(self.certificate, self.username)
        self.attributes = [{"name": "whitelist_reason", "value": "Reason for whitelisting."}]

    def test_issued_credential_type(self):
        """
        Verify issued_credential_type returns the correct credential type.
        """
        self.assertEqual(self.issuer.issued_credential_type, self.cert_type)

    def test_issue_existing_credential(self):
        """
        Verify credentials can be updated when re-issued.
        """
        user_credential = self.issuer.issue_credential(self.certificate, self.username, "revoked")
        self.user_cred.refresh_from_db()
        self._assert_usercredential_fields(self.user_cred, self.certificate, self.username, "revoked", [])
        self.assertEqual(user_credential, self.user_cred)

    def test_issue_credential_without_attributes(self):
        """
        Verify credentials can be issued without attributes.
        """
        user_credential = self.issuer.issue_credential(self.certificate, self.username)
        self._assert_usercredential_fields(user_credential, self.certificate, self.username, "awarded", [])

    def test_issue_credential_with_attributes(self):
        """
        Verify credentials can be issued with attributes.
        """
        UserFactory(username="testuser2")
        user_credential = self.issuer.issue_credential(self.certificate, "testuser2", attributes=self.attributes)
        self._assert_usercredential_fields(user_credential, self.certificate, "testuser2", "awarded", self.attributes)

    def _assert_usercredential_fields(
        self, user_credential, expected_credential, expected_username, expected_status, expected_attrs
    ):
        """Verify the fields on a UserCredential object match expectations."""
        self.assertEqual(user_credential.username, expected_username)
        self.assertEqual(user_credential.credential, expected_credential)
        self.assertEqual(user_credential.status, expected_status)
        actual_attributes = [{"name": attr.name, "value": attr.value} for attr in user_credential.attributes.all()]
        self.assertEqual(actual_attributes, expected_attrs)

    def test_set_credential_without_attributes(self):
        """
        Verify that if no attributes given then None will return.
        """
        self.assertEqual(self.issuer.set_credential_attributes(self.user_cred, None), None)

    def test_set_credential_with_attributes(self):
        """
        Verify that the system can associate credential attributes with a learner's credential.
        """
        self.issuer.set_credential_attributes(self.user_cred, self.attributes)
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, "awarded", self.attributes
        )

    def test_set_credential_with_duplicate_attributes_by_util(self):
        """
        Verify that the application throws an exception is thrown if it encounters a duplicate attribute related to a
        learner's credential.
        """
        self.attributes.append({"name": "whitelist_reason", "value": "Reason for whitelisting."})

        with self.assertRaises(DuplicateAttributeError):
            self.issuer.set_credential_attributes(self.user_cred, self.attributes)

    def test_existing_credential_with_duplicate_attributes(self):
        """
        Verify if user credential attributes already exists in db then method will update existing attributes values.
        """
        # add the attribute in db and then try to create the credential with same data "names but value is different"
        attribute_db = {"name": "whitelist_reason", "value": "Reason for whitelisting."}

        UserCredentialAttribute.objects.create(
            user_credential=self.user_cred, name=attribute_db.get("name"), value=attribute_db.get("value")
        )
        self.issuer.set_credential_attributes(self.user_cred, self.attributes)

        # first attribute value will be changed to 0.5
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, "awarded", self.attributes
        )

    def test_existing_attributes_with_empty_attributes_list(self):
        """
        Verify if user credential attributes already exists in db then in case of empty attributes list it will return
        without changing any data.
        """

        self.issuer.set_credential_attributes(self.user_cred, self.attributes)
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, "awarded", self.attributes
        )

        # create same credential without attributes.
        self.assertIsNone(self.issuer.set_credential_attributes(self.user_cred, []))
        self._assert_usercredential_fields(
            self.user_cred, self.certificate, self.user_cred.username, "awarded", self.attributes
        )


class ProgramCertificateIssuerTests(CertificateIssuerBase, TestCase):
    """
    Tests for program Issuer class and its methods.
    """

    issuer = ProgramCertificateIssuer()
    cert_factory = ProgramCertificateFactory
    cert_type = ProgramCertificate

    def setUp(self):
        super().setUp()
        self.site = SiteFactory()
        self.site_config = SiteConfigurationFactory(site=self.site)
        self.program = ProgramFactory(site=self.site, uuid=uuid4())
        self.certificate = self.cert_factory.create(
            program_uuid=self.program.uuid, program=self.program, site=self.site
        )
        self.username = "tester2"
        self.user = UserFactory(username=self.username)
        self.user_cred = self.issuer.issue_credential(self.certificate, self.username)
        self.attributes = [{"name": "whitelist_reason", "value": "Reason for whitelisting."}]

    def test_records_enabled_is_unchecked(self):
        """
        Verify that if SiteConfiguration.records_enabled is unchecked then don't send updated email to a pathway org.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        with mock.patch("credentials.apps.credentials.issuers.send_updated_emails_for_program") as mock_method:
            self.issuer.issue_credential(self.certificate, "testuser3", attributes=self.attributes)
            self.assertEqual(mock_method.call_count, 0)

    def test_records_enabled_is_checked(self):
        """
        Verify that if SiteConfiguration.records_enabled is checked and new record is created then updated email is
        sent to a pathway org.
        """
        with mock.patch("credentials.apps.credentials.issuers.send_updated_emails_for_program") as mock_method:
            self.issuer.issue_credential(self.certificate, "testuser4", attributes=self.attributes)
            self.assertEqual(mock_method.call_count, 1)

    @override_settings(SEND_EMAIL_ON_PROGRAM_COMPLETION=True)
    @mock.patch("credentials.apps.credentials.issuers.send_program_certificate_created_message")
    def test_send_learner_email_when_issuing_program_cert(self, mock_send_learner_email):
        """
        Verify that the application sends a program completion email when a learner is issued a credential for the first
        time.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        self.issuer.issue_credential(self.certificate, "testuser5", lms_user_id=123)
        self.assertEqual(mock_send_learner_email.call_count, 1)

    @override_settings(SEND_EMAIL_ON_PROGRAM_COMPLETION=True)
    @mock.patch("credentials.apps.credentials.issuers.send_program_certificate_created_message")
    def test_send_learner_email_only_once(self, mock_send_learner_email):
        """
        Verify that the application will not send additional program completion emails if the certificate is modified
        after originally being issued.
        """
        username = "learner"
        user = UserFactory(username=username)

        self.site_config.records_enabled = False
        self.site_config.save()

        self.issuer.issue_credential(self.certificate, user.username, lms_user_id=123)
        # revoke the user credential
        user_credential = UserCredential.objects.get(username=username)
        user_credential.revoke()
        # issue the credential again, make sure that we haven't tried to send the email again
        self.issuer.issue_credential(self.certificate, user.username, lms_user_id=123)
        self.assertEqual(mock_send_learner_email.call_count, 1)

    @override_settings(SEND_EMAIL_ON_PROGRAM_COMPLETION=False)
    @mock.patch("credentials.apps.credentials.issuers.send_program_certificate_created_message")
    def test_do_not_send_learner_email_when_feature_disabled(self, mock_send_learner_email):
        """
        Verify that we don't try to send an updated program progress email when issuing an updated program credential.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        self.issuer.issue_credential(self.certificate, "testuser6")
        self.assertEqual(mock_send_learner_email.call_count, 0)

    @mock.patch("credentials.apps.credentials.issuers.ProgramCertificateIssuer._emit_program_certificate_signal")
    def test_publish_program_certificate_signal(self, mock_emit):
        """
        Verify that the ProgramCertificateIssuer makes a call to the `_emit_program_certificate_signal` function as
        expected when the system creates or updates a UserCredential.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        user = UserFactory()
        self.issuer.issue_credential(self.certificate, user.username)

        # retrieve the credential generated for verifications
        user_credential = UserCredential.objects.get(username=user.username, credential_id=self.certificate.id)
        assert mock_emit.call_count == 1
        mock_emit.assert_called_with(user.username, user_credential, "awarded", self.certificate)

    @override_settings(SEND_PROGRAM_CERTIFICATE_AWARDED_SIGNAL=True)
    @mock.patch("credentials.apps.credentials.issuers.PROGRAM_CERTIFICATE_AWARDED.send_event")
    def test_emit_program_certificate_signal_certificate_awarded(self, mock_send):
        """
        Verify that a `PROGRAM_CERTIFICATE_AWARDED` signal is emit when a program certificate is awarded to a learner.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        user = UserFactory()
        self.issuer.issue_credential(self.certificate, user.username)
        user_credential = UserCredential.objects.get(username=user.username, credential_id=self.certificate.id)

        expected_event_data = ProgramCertificateData(
            user=UserData(
                pii=UserPersonalData(username=user.username, email=user.email, name=user.get_full_name()),
                id=user.lms_user_id,
                is_active=user.is_active,
            ),
            program=ProgramData(
                uuid=str(self.program.uuid), title=self.program.title, program_type=self.program.type_slug
            ),
            uuid=str(user_credential.uuid),
            status="awarded",
            url=f"https://{self.site.domain}/credentials/{str(user_credential.uuid).replace('-', '')}/",
        )

        assert mock_send.call_count == 1
        mock_call_args = mock_send.mock_calls[0].kwargs
        assert expected_event_data == mock_call_args["program_certificate"]

    @override_settings(SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL=True)
    @mock.patch("credentials.apps.credentials.issuers.PROGRAM_CERTIFICATE_REVOKED.send_event")
    def test_emit_program_certificate_signal_certificate_revoked(self, mock_send):
        """
        Verify that a `PROGRAM_CERTIFICATE_REVOKED` signal is emit when a program certificate is revoked from a learner.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        user = UserFactory()
        self.issuer.issue_credential(self.certificate, user.username, UserCredentialStatus.REVOKED)
        user_credential = UserCredential.objects.get(username=user.username, credential_id=self.certificate.id)

        expected_event_data = ProgramCertificateData(
            user=UserData(
                pii=UserPersonalData(username=user.username, email=user.email, name=user.get_full_name()),
                id=user.lms_user_id,
                is_active=user.is_active,
            ),
            program=ProgramData(
                uuid=str(self.program.uuid), title=self.program.title, program_type=self.program.type_slug
            ),
            uuid=str(user_credential.uuid),
            status="revoked",
            url=f"https://{self.site.domain}/credentials/{str(user_credential.uuid).replace('-', '')}/",
        )

        assert mock_send.call_count == 1
        mock_call_args = mock_send.mock_calls[0].kwargs
        assert expected_event_data == mock_call_args["program_certificate"]

    @override_settings(SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL=False)
    @mock.patch("credentials.apps.credentials.issuers.PROGRAM_CERTIFICATE_REVOKED.send_event")
    def test_emit_program_certificate_signal_certificate_revoked_signal_disabled(self, mock_send):
        """
        Verify that a `PROGRAM_CERTIFICATE_REVOKED` signal is NOT emit if the `SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL`
        feature flag is disabled.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        user = UserFactory()
        self.issuer.issue_credential(self.certificate, user.username)
        user_credential = UserCredential.objects.get(username=user.username, credential_id=self.certificate.id)

        assert user_credential
        assert mock_send.call_count == 0

    @override_settings(SEND_PROGRAM_CERTIFICATE_AWARDED_SIGNAL=True)
    @mock.patch("credentials.apps.credentials.issuers.PROGRAM_CERTIFICATE_AWARDED.send_event")
    def test_emit_program_certificate_signal_user_dne(self, mock_send):
        """
        Verify error handling and application behavior if the system cannot retrieve a user with the specified username
        when attempting to send a program certificate event.
        """
        self.site_config.records_enabled = False
        self.site_config.save()

        expected_error_message = (
            "Unable to send a program certificate event for user with username [mistadobalina]. No user found "
            "matching this username"
        )

        with LogCapture() as log:
            self.issuer.issue_credential(self.certificate, "mistadobalina")

        assert expected_error_message in log.records[0].msg
        assert mock_send.call_count == 0


class CourseCertificateIssuerTests(CertificateIssuerBase, TestCase):
    """
    Tests for course Issuer class and its methods.
    """

    issuer = CourseCertificateIssuer()
    cert_factory = CourseCertificateFactory
    cert_type = CourseCertificate
