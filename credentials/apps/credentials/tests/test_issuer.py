"""
Tests for Issuer class.
"""
# pylint: disable=no-member
import ddt
from django.test import TestCase

from credentials.apps.api.exceptions import DuplicateAttributeError
from credentials.apps.credentials.issuers import ProgramCertificateIssuer
from credentials.apps.credentials.models import ProgramCertificate, UserCredentialAttribute
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory

LOGGER_NAME = 'credentials.apps.credentials.issuers'


@ddt.ddt
class ProgramCertificateIssuerTests(TestCase):
    """ Tests for Issuer class and its methods."""

    def setUp(self):
        super(ProgramCertificateIssuerTests, self).setUp()
        self.issuer = ProgramCertificateIssuer()
        self.program_certificate = ProgramCertificateFactory.create()
        self.username = 'tester'
        self.user_program_cred = self.issuer.issue_credential(self.program_certificate, self.username)
        self.attributes = [{"name": "whitelist_reason", "value": "Reason for whitelisting."}]

    def test_issued_credential_type(self):
        """ Verify issued_credential_type returns the correct credential type."""
        self.assertEqual(self.issuer.issued_credential_type, ProgramCertificate)

    def test_issue_credential_without_attributes(self):
        """ Verify credentials can be issued without attributes."""

        user_credential = self.issuer.issue_credential(self.program_certificate, self.username)
        self._assert_usercredential_fields(user_credential, self.program_certificate, self.username, [])

    def test_issue_credential_with_attributes(self):
        """ Verify credentials can be issued with attributes."""

        user_credential = self.issuer.issue_credential(self.program_certificate, 'testuser2', self.attributes)
        self._assert_usercredential_fields(user_credential, self.program_certificate, 'testuser2', self.attributes)

    def _assert_usercredential_fields(self, user_credential, expected_credential, expected_username, expected_attrs):  # pylint: disable=line-too-long
        """ Verify the fields on a UserCredential object match expectations. """
        self.assertEqual(user_credential.username, expected_username)
        self.assertEqual(user_credential.credential, expected_credential)
        actual_attributes = [{'name': attr.name, 'value': attr.value} for attr in user_credential.attributes.all()]
        self.assertEqual(actual_attributes, expected_attrs)

    def test_set_credential_without_attributes(self):
        """ Verify that if no attributes given then None will return."""
        self.assertEqual(
            self.issuer.set_credential_attributes(self.user_program_cred, None),
            None
        )

    def test_set_credential_with_attributes(self):
        """ Verify that it adds the given attributes against user credential."""

        self.issuer.set_credential_attributes(self.user_program_cred, self.attributes)
        self._assert_usercredential_fields(
            self.user_program_cred, self.program_certificate, self.user_program_cred.username, self.attributes
        )

    def test_set_credential_with_duplicate_attributes_by_util(self):
        """Verify in case of duplicate attributes utils method will return False and
        exception will be raised.
        """

        self.attributes.append({"name": "whitelist_reason", "value": "Reason for whitelisting."})

        with self.assertRaises(DuplicateAttributeError):
            self.issuer.set_credential_attributes(self.user_program_cred, self.attributes)

    def test_existing_credential_with_duplicate_attributes(self):
        """Verify if user credential attributes already exists in db then method will
        update existing attributes values."""

        # add the attribute in db and then try to create the credential
        # with same data "names but value is different"

        attribute_db = {"name": "whitelist_reason", "value": "Reason for whitelisting."}

        UserCredentialAttribute.objects.create(
            user_credential=self.user_program_cred,
            name=attribute_db.get("name"),
            value=attribute_db.get("value")
        )
        self.issuer.set_credential_attributes(self.user_program_cred, self.attributes)

        # first attribute value will be changed to 0.5
        self._assert_usercredential_fields(
            self.user_program_cred,
            self.program_certificate,
            self.user_program_cred.username,
            self.attributes
        )

    def test_existing_attributes_with_empty_attributes_list(self):
        """Verify if user credential attributes already exists in db then in case of empty
        attributes list it will return without changing any data."""

        self.issuer.set_credential_attributes(self.user_program_cred, self.attributes)
        self._assert_usercredential_fields(
            self.user_program_cred, self.program_certificate, self.user_program_cred.username, self.attributes
        )

        # create same credential without attributes.
        self.assertIsNone(self.issuer.set_credential_attributes(self.user_program_cred, []))
        self._assert_usercredential_fields(
            self.user_program_cred, self.program_certificate, self.user_program_cred.username, self.attributes
        )
