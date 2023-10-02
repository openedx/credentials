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
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory
from credentials.apps.verifiable_credentials.storages.learner_credential_wallet import LCWallet

from ..models import IssuanceConfiguration, IssuanceLine


class IssuanceLineTestCase(SiteMixin, TestCase):
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
        self.issuance_line = IssuanceLineFactory.create(
            user_credential=self.program_user_credential,
            status_index=5,
            storage_id=LCWallet.ID,
            issuer_id="test-issuer-id-2",
        )

    @mock.patch("credentials.apps.verifiable_credentials.issuance.models.get_storage")
    def test_storage_property(self, mock_get_storage):
        self.issuance_line.storage  # pylint: disable=pointless-statement
        mock_get_storage.assert_called_with(self.issuance_line.storage_id)

    @mock.patch("credentials.apps.verifiable_credentials.issuance.models.get_data_model")
    def test_data_model_property(self, mock_get_data_model):
        self.issuance_line.data_model  # pylint: disable=pointless-statement
        mock_get_data_model.assert_called_with(self.issuance_line.data_model_id)

    @mock.patch("credentials.apps.verifiable_credentials.issuance.utils.get_issuer")
    def test_issuer_name_property(self, mock_get_issuer):
        self.issuance_line.issuer_name  # pylint: disable=pointless-statement
        mock_get_issuer.assert_called_with(self.issuance_line.issuer_id)

    def test_finalize(self):
        self.issuance_line.processed = False
        self.issuance_line.save()
        self.assertFalse(self.issuance_line.processed)
        self.issuance_line.finalize()
        self.assertTrue(self.issuance_line.processed)

    @mock.patch("credentials.apps.verifiable_credentials.issuance.models.get_current_request")
    def test_get_status_list_url(self, mock_get_current_request):
        mock_request = APIRequestFactory(SERVER_NAME=self.site.domain).get("/api/v1/endpoint/")
        mock_request.path = "/api/v1/endpoint/"
        mock_get_current_request.return_value = mock_request

        status_list_url = self.issuance_line.get_status_list_url()
        self.assertEqual(
            status_list_url,
            f"http://{self.site.domain}/verifiable_credentials/api/v1/status-list/2021/v1/test-issuer-id-2/",
        )

        status_list_url_with_hash = self.issuance_line.get_status_list_url(hash_str="test-hash")
        self.assertEqual(
            status_list_url_with_hash,
            f"http://{self.site.domain}/verifiable_credentials/api/v1/status-list/2021/v1/test-issuer-id-2/#test-hash",
        )

    @mock.patch("credentials.apps.verifiable_credentials.issuance.utils.get_default_issuer")
    def test_resolve_issuer(self, mock_get_default_issuer):
        IssuanceLine.resolve_issuer()
        mock_get_default_issuer.assert_called_once()

    def test_get_next_status_index_first(self):
        IssuanceLine.objects.all().delete()
        next_status_index = IssuanceLine.get_next_status_index("test-issuer-id")
        self.assertEqual(next_status_index, 0)

    def test_get_next_status_index_not_first(self):
        IssuanceLineFactory.create(issuer_id="test-issuer-id", status_index=2)
        next_status_index = IssuanceLine.get_next_status_index("test-issuer-id")
        self.assertEqual(next_status_index, 3)

    def test_get_indicies_for_status(self):
        IssuanceLineFactory.create(
            issuer_id="test-issuer-id",
            processed=True,
            user_credential__status=UserCredentialStatus.AWARDED,
            status_index=3,
        )

        IssuanceLineFactory.create(
            issuer_id="test-issuer-id",
            processed=True,
            user_credential__status=UserCredentialStatus.REVOKED,
            status_index=4,
        )

        indicies = IssuanceLine.get_indicies_for_status(issuer_id="test-issuer-id", status=UserCredentialStatus.REVOKED)
        self.assertEqual(indicies, [4])


class IssuanceConfigurationTestCase(SiteMixin, TestCase):
    def test_create_issuers_new_issuer(self):
        IssuanceConfiguration.create_issuers()
        issuance_configuration = IssuanceConfiguration.objects.last()
        self.assertIsNotNone(issuance_configuration)
        self.assertTrue(issuance_configuration.enabled)
        self.assertEqual(issuance_configuration.issuer_id, "test-issuer-did")
        self.assertEqual(issuance_configuration.issuer_key, "test-issuer-key")
        self.assertEqual(issuance_configuration.issuer_name, "test-issuer-name")
