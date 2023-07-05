from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory
from credentials.apps.verifiable_credentials.storages.learner_credential_wallet import LCWallet

from ..verifiable_credentials import VerifiableCredentialsDataModel


class VerifiableCredentialsTestCase(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.program_cert = ProgramCertificateFactory.create(program_uuid=self.program.uuid, site=self.site)
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        self.program_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert,
        )
        self.issuance_line_program_certificate = IssuanceLineFactory.create(
            user_credential=self.program_user_credential,
            status_index=1,
            storage_id=LCWallet.ID,
            issuer_id="test-issuer-id-1",
        )

    def test_get_context(self):
        context = VerifiableCredentialsDataModel().get_context()
        self.assertEqual(context, ["https://schema.org/"])

    def test_resolve_credential_type_with_valid_type(self):
        credential_type = VerifiableCredentialsDataModel().resolve_credential_type(
            self.issuance_line_program_certificate
        )
        self.assertEqual(credential_type, ["EducationalOccupationalCredential"])

    def test_resolve_credential_type_with_no_user_credential(self):
        issuance_line_without_credential = IssuanceLineFactory.create(
            user_credential=None,
        )
        credential_types = VerifiableCredentialsDataModel().resolve_credential_type(issuance_line_without_credential)
        self.assertEqual(credential_types, [])
