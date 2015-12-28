"""
Tests for Accreditor class.
"""
from django.test import TestCase
from mock import patch
from testfixtures import LogCapture

from credentials.apps.api.accreditor import Accreditor
from credentials.apps.api.exceptions import UnsupportedCredentialTypeError
from credentials.apps.credentials.issuers import ProgramCertificateIssuer
from credentials.apps.credentials.models import ProgramCertificate


LOGGER_NAME = 'credentials.apps.api.accreditor'


class TestAccreditor(TestCase):
    """ Tests for Accreditor class. This class is responsible to call the right
    credential issuer class to generate the credential.
    """

    def setUp(self):
        super(TestAccreditor, self).setUp()
        self.accreditor = Accreditor()
        self.program_content_type = ProgramCertificate.credential_type_slug
        self.data = {
            "program_id": 10,
            "attributes": [{"namespace": "whitelist", "name": "grade", "value": "0.5"}]
        }
        self.slug = ProgramCertificateIssuer.issued_credential_type.credential_type_slug

    def test_create_credential_type_issuer_map(self):
        """ Verify that credential_type_issuer_map unique credential type. """
        accreditor = Accreditor(issuers=[ProgramCertificateIssuer(), ProgramCertificateIssuer()])
        self.assertDictEqual(
            accreditor.credential_type_issuer_map, {
                self.slug: accreditor.issuers[0]
            }
        )

    def test_issue_credential_with_invalid_type(self):
        """ Verify that issue credential does not work with if credential type is invalid. """
        with self.assertRaises(UnsupportedCredentialTypeError):
            __ = self.accreditor.issue_credential('dummy', 'tester', **self.data)

    def test_issue_credential_method(self):
        """ Verify that issue_credential() called and issues credential."""
        with patch.object(ProgramCertificateIssuer, 'issue_credential') as mock_method:
            self.accreditor.issue_credential(self.program_content_type, 'tester', **self.data)
            mock_method.assert_called_with('tester', **self.data)

    def test_credential_with_duplicate_slug_type(self):
        """ Verify that if duplicate slug types appear than warning will be
        logged.
        ."""
        # Verify log is captured.
        msg = 'Issuer slug type already exist [{type}].'.format(
            type=ProgramCertificateIssuer.issued_credential_type.credential_type_slug
        )
        with LogCapture(LOGGER_NAME) as l:
            # Pass duplicate issuers to capture the log.
            accreditor = Accreditor(issuers=[ProgramCertificateIssuer(), ProgramCertificateIssuer()])
            l.check((LOGGER_NAME, 'WARNING', msg))
            self.assertDictEqual(
                accreditor.credential_type_issuer_map, {
                    self.slug: accreditor.issuers[0]
                }
            )
