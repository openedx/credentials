"""
Tests for the accreditor module.
"""

from django.test import TestCase
from mock import patch
from testfixtures import LogCapture

from credentials.apps.api.accreditors import Accreditor
from credentials.apps.api.exceptions import UnsupportedCredentialTypeError
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.issuers import CourseCertificateIssuer, ProgramCertificateIssuer
from credentials.apps.credentials.models import CourseCertificate, ProgramCertificate
from credentials.apps.credentials.tests.factories import CourseCertificateFactory, ProgramCertificateFactory

LOGGER_NAME = 'credentials.apps.api.accreditors'


class AccreditorTests(SiteMixin, TestCase):
    attributes = [{'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'}]
    course_credential = CourseCertificate
    program_credential = ProgramCertificate

    def setUp(self):
        super().setUp()
        self.program_cert = ProgramCertificateFactory()

    def test_create_credential_type_issuer_map(self):
        """ Verify the Accreditor supports only one issuer per credential type. """
        accreditor = Accreditor(issuers=[ProgramCertificateIssuer(), ProgramCertificateIssuer()])

        expected = {
            self.program_credential: accreditor.issuers[0]
        }
        self.assertEqual(accreditor.credential_type_issuer_map, expected)

    def test_issue_credential_with_invalid_type(self):
        """ Verify the method raises an error for attempts to issue an unsupported credential type. """
        accreditor = Accreditor(issuers=[ProgramCertificateIssuer()])
        course_cert = CourseCertificateFactory()
        with self.assertRaises(UnsupportedCredentialTypeError):
            accreditor.issue_credential(self.site, course_cert, 'tester', attributes=self.attributes)

    def test_issue_credential(self):
        """ Verify the method calls the Issuer's issue_credential method. """
        accreditor = Accreditor(issuers=[ProgramCertificateIssuer()])
        with patch.object(ProgramCertificateIssuer, 'issue_credential') as mock_method:
            accreditor.issue_credential(self.site, self.program_cert, 'tester', attributes=self.attributes)
            mock_method.assert_called_with(self.site, self.program_cert, 'tester', 'awarded', self.attributes)

    def test_constructor_with_multiple_issuers_for_same_credential_type(self):
        """ Verify the Accreditor supports a single Issuer per credential type.
        Attempts to register additional issuers for a credential type should
        result in a warning being logged.
        """
        msg = 'The issuer [{}] is already registered to issue credentials of type [{}]. [{}] will NOT be used.'.format(
            ProgramCertificateIssuer, self.program_credential, ProgramCertificateIssuer
        )

        with LogCapture(LOGGER_NAME) as l:
            accreditor = Accreditor(issuers=[ProgramCertificateIssuer(), ProgramCertificateIssuer()])
            l.check((LOGGER_NAME, 'WARNING', msg))
        expected = {self.program_credential: accreditor.issuers[0]}
        self.assertEqual(accreditor.credential_type_issuer_map, expected)

    def test_constructor_with_multiple_issuers(self):
        """ Verify the Accreditor supports multiple Issuers """
        accreditor = Accreditor(issuers=[CourseCertificateIssuer(), ProgramCertificateIssuer()])

        expected = {
            self.course_credential: accreditor.issuers[0],
            self.program_credential: accreditor.issuers[1],
        }
        self.assertDictEqual(accreditor.credential_type_issuer_map, expected)
