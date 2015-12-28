"""
Tests for Issuer class.
"""
import ddt
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase
from testfixtures import LogCapture

from credentials.apps.api.tests.factories import ProgramCertificateFactory
from credentials.apps.credentials.issuers import ProgramCertificateIssuer
from credentials.apps.credentials.models import ProgramCertificate, UserCredential

LOGGER_NAME = 'credentials.apps.credentials.issuers'


@ddt.ddt
class TestProgramCertificateIssuer(TestCase):
    """ Tests for Issuer class and its methods. For incoming credential request
    issuer class is responsible to generate the credential. This is atomic operation and
    in case of any error data will be roll backed.
    """
    def setUp(self):
        super(TestProgramCertificateIssuer, self).setUp()
        self.issuer = ProgramCertificateIssuer()
        self.program_certificate = ProgramCertificateFactory.create()
        self.username = 'tester'
        self.data = {
            "program_id": self.program_certificate.program_id,
            "attributes": [{"namespace": "whitelist", "name": "grade", "value": "0.5"}]
        }

    def test_issuer_type(self):
        """ Verify ProgramsCertificateIssuer has valid issuer type. """
        self.assertEqual(self.issuer.issued_credential_type, ProgramCertificate)

    def test_issue_credential(self):
        """ Verify issue_credential issues user credential for given user. """
        isseued_credential = self.issuer.issue_credential(self.username, **self.data)
        db_credential = UserCredential.objects.get(username=self.username)
        self._assert_values(isseued_credential, db_credential)

        attrs = db_credential.attributes.all()[0]
        self.assertEqual(attrs.namespace, 'whitelist')
        self.assertEqual(attrs.name, 'grade')
        self.assertEqual(attrs.value, '0.5')

    def test_issue_credential_with_missing_attributes(self):
        """ Verify issue_credential issues credential even if attributes
        dict is empty any field any field is missing.
        """
        # data without namespace and reason.
        data = {
            "program_id": self.program_certificate.program_id,
            "attributes": [{"name": "Whitelist"}]
        }

        isseued_credential = self.issuer.issue_credential(self.username, **data)
        db_credential = UserCredential.objects.get(username=self.username)
        self._assert_values(isseued_credential, db_credential)
        self.assertFalse(db_credential.attributes.exists())

    def test_issue_credential_with_duplicate_attributes(self):
        """ Verify issuer raises exception and rolled backed the whole
        operation in case of duplicate attributes.
        """

        data = {
            "program_id": self.program_certificate.program_id,
            "attributes": [
                {"namespace": "whitelist2", "name": "grade", "value": "0.5"},
                {"namespace": "whitelist2", "name": "grade", "value": "0.5"}
            ]
        }
        with self.assertRaises(IntegrityError):
            self.issuer.issue_credential(self.username, **data)
        self.assertFalse(UserCredential.objects.filter(username=self.username).exists())

    def test_credential_already_exists(self):
        """ Verify that credential will not be issued if user has already issued credential."""
        self.issuer.issue_credential(self.username, **self.data)

        # Create credentials with same information.
        self.issuer.issue_credential(self.username, **self.data)

        # Verify only one record exists in database.
        self.assertEqual(UserCredential.objects.all().count(), 1)

        # Verify log is captured.
        msg = 'User [{username}] already has a credential for program [{program_id}].'.format(
            username=self.username, program_id=self.program_certificate.program_id)
        with LogCapture(LOGGER_NAME) as l:
            self.issuer.issue_credential(self.username, **self.data)
            l.check((LOGGER_NAME, 'WARNING', msg))

    def _assert_values(self, isseued_credential, db_credential):
        """ DRY function for credentials assertions."""
        self.assertEqual(isseued_credential, db_credential)
        self.assertEqual(db_credential.username, self.username)
        self.assertEqual(
            db_credential.credential_content_type,
            ContentType.objects.get_for_model(ProgramCertificate)
        )
        self.assertEqual(UserCredential.objects.all().count(), 1)

    @ddt.data(
        ([], 7, 0),
        ([{"namespace": "whitelist1", "name": "grade", "value": "0.5"}], 8, 1),
        ([
            {"namespace": "whitelist2", "name": "grade", "value": "0.5"},
            {"namespace": "whitelist3", "name": "grade", "value": "0.5"}
        ], 8, 2),
    )
    @ddt.unpack
    def test_issue_credential_queries(self, attrs, queries, attrs_count):
        """ Verify issue_credential issues user credential for given user. """
        self.data['attributes'] = attrs
        with self.assertNumQueries(queries):
            issued_credential = self.issuer.issue_credential(self.username, **self.data)

        db_credential = UserCredential.objects.get(username=self.username)
        self._assert_values(issued_credential, db_credential)
        self.assertEqual(db_credential.attributes.count(), attrs_count)
