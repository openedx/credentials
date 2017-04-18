"""
Tests for the accreditor module.
"""

from django.test import TestCase
from mock import patch
from testfixtures import LogCapture

from credentials.apps.api.accreditors import Accreditor
from credentials.apps.api.exceptions import UnsupportedCredentialTypeError
from credentials.apps.credentials.issuers import ProgramCertificateIssuer
from credentials.apps.credentials.models import ProgramCertificate
from credentials.apps.credentials.tests.factories import CourseCertificateFactory, ProgramCertificateFactory

LOGGER_NAME = 'credentials.apps.api.accreditors'


class AccreditorTests(TestCase):
    """ Tests for Accreditor class. This class is responsible to call the right
    credential issuer class to generate the credential.
    """

    def setUp(self):
        super(AccreditorTests, self).setUp()
        self.accreditor = Accreditor()
        self.program_cert = ProgramCertificateFactory()
        self.program_credential = ProgramCertificate
        self.attributes = [{"name": "whitelist_reason", "value": "Reason for whitelisting."}]

    def test_create_credential_type_issuer_map(self):
        """ Verify the Accreditor supports only one issuer per credential type. """
        accreditor = Accreditor(issuers=[ProgramCertificateIssuer(), ProgramCertificateIssuer()])

        expected = {
            self.program_credential: accreditor.issuers[0]
        }
        self.assertEqual(accreditor.credential_type_issuer_map, expected)

    def test_issue_credential_with_invalid_type(self):
        """ Verify the method raises an error for attempts to issue an unsupported credential type. """
        course_cert = CourseCertificateFactory()
        with self.assertRaises(UnsupportedCredentialTypeError):
            self.accreditor.issue_credential(course_cert, 'tester', self.attributes)

    def test_issue_credential(self):
        """ Verify the method calls the Issuer's issue_credential method. """
        with patch.object(ProgramCertificateIssuer, 'issue_credential') as mock_method:
            self.accreditor.issue_credential(self.program_cert, 'tester', self.attributes)
            mock_method.assert_called_with(self.program_cert, 'tester', self.attributes)

    def test_constructor_with_multiple_issuers_for_same_credential_type(self):
        """ Verify the Accreditor supports a single Issuer per credential type.
        Attempts to register additional issuers for a credential type should
        result in a warning being logged.
        """
        msg = "The issuer [{}] is already registered to issue credentials of type [{}]. [{}] will NOT be used.".format(
            ProgramCertificateIssuer, self.program_credential, ProgramCertificateIssuer
        )

        with LogCapture(LOGGER_NAME) as l:
            accreditor = Accreditor(issuers=[ProgramCertificateIssuer(), ProgramCertificateIssuer()])
            l.check((LOGGER_NAME, 'WARNING', msg))
        expected = {self.program_credential: accreditor.issuers[0]}
        self.assertEqual(accreditor.credential_type_issuer_map, expected)
