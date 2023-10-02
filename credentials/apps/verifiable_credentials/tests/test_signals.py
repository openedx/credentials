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
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory
from credentials.apps.verifiable_credentials.storages.learner_credential_wallet import LCWallet


class SignalsTestCase(SiteMixin, TestCase):
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
            status=UserCredentialStatus.REVOKED,
        )
        self.issuance_line = IssuanceLineFactory.create(
            user_credential=self.program_user_credential,
            status=UserCredentialStatus.REVOKED,
            status_index=5,
            storage_id=LCWallet.ID,
        )
        self.issuance_line_2 = IssuanceLineFactory.create(
            user_credential=self.program_user_credential,
            status=UserCredentialStatus.REVOKED,
            status_index=6,
            storage_id=LCWallet.ID,
        )

    def test_update_issuance_lines(self):
        self.program_user_credential.status = UserCredentialStatus.AWARDED
        self.program_user_credential.save()

        self.issuance_line.refresh_from_db()
        self.issuance_line_2.refresh_from_db()

        self.assertEqual(self.issuance_line.status, UserCredentialStatus.AWARDED)
        self.assertEqual(self.issuance_line_2.status, UserCredentialStatus.AWARDED)
