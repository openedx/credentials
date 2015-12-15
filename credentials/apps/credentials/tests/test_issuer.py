"""
Tests for Issuer class.
"""
# pylint: disable=no-member
import ddt
from django.test import TestCase
from testfixtures import LogCapture
from credentials.apps.api.exceptions import DuplicateAttributeError

from credentials.apps.api.tests.factories import ProgramCertificateFactory
from credentials.apps.credentials.issuers import ProgramCertificateIssuer
from credentials.apps.credentials.models import (
    ProgramCertificate,
    UserCredential,
    UserCredentialAttribute
)


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
        self.attributes = [
            {"namespace": "whitelist1", "name": "grade", "value": "0.5"},
            {"namespace": "whitelist2", "name": "grade", "value": "0.5"}
        ]

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

    def test_credential_already_exists(self):
        """ Verify that credential will not be issued if user has already issued credential."""
        self.issuer.issue_credential(self.program_certificate, self.username, self.attributes)

        # Create credentials with same information.
        self.issuer.issue_credential(self.program_certificate, self.username, self.attributes)

        # Verify only one record exists in database.
        self.assertEqual(UserCredential.objects.all().count(), 1)

        # Verify log is captured.
        msg = 'User [{username}] already has a credential for program [{program_id}].'.format(
            username=self.username, program_id=self.program_certificate.program_id)
        with LogCapture(LOGGER_NAME) as l:
            self.issuer.issue_credential(self.program_certificate, self.username, self.attributes)
            l.check((LOGGER_NAME, 'WARNING', msg))

    def _assert_usercredential_fields(self, user_credential, expected_credential, expected_username, expected_attrs):  # pylint: disable=line-too-long
        """ Verify the fields on a UserCredential object match expectations. """
        self.assertEqual(user_credential.username, expected_username)
        self.assertEqual(user_credential.credential, expected_credential)
        actual_attributes = [
            {'namespace': attr.namespace, 'name': attr.name, 'value': attr.value}
            for attr in user_credential.attributes.all()
        ]
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
        self.attributes[0].update({'namespace': 'whitelist2'})

        with self.assertRaises(DuplicateAttributeError):
            self.issuer.set_credential_attributes(self.user_program_cred, self.attributes)

    def test_set_credential_with_duplicate_attributes_by_db(self):
        """Verify in case of duplicate attributes if any existing record was in db
        then exception will be raised.
        """
        # add the attribute in db and then try to create the credential
        # with same data. In this case get_or_create will return False.

        UserCredentialAttribute.objects.create(
            user_credential=self.user_program_cred,
            namespace="whitelist1",
            name="grade",
            value="0.8"
        )

        with self.assertRaises(DuplicateAttributeError):
            self.issuer.set_credential_attributes(self.user_program_cred, self.attributes)
