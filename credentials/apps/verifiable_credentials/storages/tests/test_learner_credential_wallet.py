from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIRequestFactory

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

from ..learner_credential_wallet import LCWallet


class LearnerCredentialWalletStorageTestCase(SiteMixin, TestCase):
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
        self.issuance_line = IssuanceLineFactory.create(user_credential=self.program_user_credential, status_index=5)

    @mock.patch("credentials.apps.verifiable_credentials.storages.learner_credential_wallet.get_current_request")
    def test_get_deeplink_url(self, mock_get_current_request):
        mock_get_current_request.return_value = APIRequestFactory().get("/")
        deeplink_url = LCWallet.get_deeplink_url(self.issuance_line)
        self.assertIsNotNone(deeplink_url)
        self.assertIn(LCWallet.DEEP_LINK_URL, deeplink_url)
        self.assertIn("issuer", deeplink_url)
        self.assertIn("vc_request_url", deeplink_url)
        self.assertIn("auth_type", deeplink_url)
        self.assertIn("challenge", deeplink_url)
