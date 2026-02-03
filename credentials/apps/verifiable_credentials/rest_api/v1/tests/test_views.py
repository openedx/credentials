import json
from unittest import mock

from ddt import data, ddt, unpack
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.verifiable_credentials.issuance import IssuanceException
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory
from credentials.apps.verifiable_credentials.storages.learner_credential_wallet import LCWallet
from credentials.apps.verifiable_credentials.utils import get_user_credentials_data

JSON_CONTENT_TYPE = "application/json"


@ddt
class ProgramCredentialsViewTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.course_certs = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program=self.program,
            program_uuid=self.program.uuid,
            site=self.site,
        )
        self.course_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="coursecertificate"
        )
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        self.course_user_credentials = [
            UserCredentialFactory.create(
                username=self.user.username,
                credential_content_type=self.course_credential_content_type,
                credential=course_cert,
            )
            for course_cert in self.course_certs
        ]
        self.program_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert,
        )

    def test_deny_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get("/verifiable_credentials/api/v1/credentials/")
        self.assertEqual(response.status_code, 401)

    def test_allow_authenticated_user(self):
        """Verify the endpoint requires an authenticated user."""
        self.client.logout()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        response = self.client.get("/verifiable_credentials/api/v1/credentials/")
        self.assertEqual(response.status_code, 200)

    def test_get_without_query_params(self):
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        response = self.client.get("/verifiable_credentials/api/v1/credentials/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["program_credentials"], get_user_credentials_data(self.user.username, "programcertificate")
        )
        self.assertEqual(
            response.data["course_credentials"], get_user_credentials_data(self.user.username, "coursecertificate")
        )

    @data(
        ("programcertificate", {"program_credentials": "programcertificate"}, ["course_credentials"]),
        ("coursecertificate", {"course_credentials": "coursecertificate"}, ["program_credentials"]),
        (
            "programcertificate,coursecertificate",
            {"program_credentials": "programcertificate", "course_credentials": "coursecertificate"},
            [],
        ),
    )
    @unpack
    def test_get_with_query_params(self, types, expected_data, not_in_keys):
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        response = self.client.get(f"/verifiable_credentials/api/v1/credentials/?types={types}")
        self.assertEqual(response.status_code, 200)

        for key, expected_value in expected_data.items():
            self.assertEqual(response.data[key], get_user_credentials_data(self.user.username, expected_value))

        for key in not_in_keys:
            self.assertNotIn(key, response.data)


class InitIssuanceViewTestCase(SiteMixin, TestCase):
    url_path = reverse("verifiable_credentials:api:v1:credentials-init")

    def setUp(self):
        super().setUp()
        self.url = "/verifiable_credentials/api/v1/credentials/init/"
        self.user = UserFactory()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.course_certs = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                course_run=course_run,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.program_cert = ProgramCertificateFactory.create(
            program=self.program,
            program_uuid=self.program.uuid,
            site=self.site,
        )
        self.program_credential_content_type = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        self.program_user_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert,
        )
        self.data = {
            "credential_uuid": str(self.program_user_credential.uuid),
            "storage_id": LCWallet.ID,
        }

    def authenticate_user(self, user):
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def test_authentication(self):
        self.client.logout()
        response = self.client.post(self.url_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

        self.authenticate_user(self.user)
        response = self.client.post(self.url_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200)

    def test_post_with_correct_data(self):
        self.authenticate_user(self.user)
        response = self.client.post(self.url_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        expected_properties = ["app_link_android", "app_link_ios", "deeplink", "qrcode"]
        self.assertEqual(response.status_code, 200)
        for property_name in expected_properties:
            self.assertIn(property_name, response.data)
            self.assertIsNotNone(response.data.get(property_name))

    def test_post_with_incorrect_data(self):
        self.authenticate_user(self.user)
        response = self.client.post(
            self.url_path, data=json.dumps({"storage_id": "test-storage-id"}), content_type=JSON_CONTENT_TYPE
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            self.url_path,
            data=json.dumps({"credential_uuid": "non-valid-credential-id"}),
            content_type=JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            self.url_path,
            data=json.dumps({"credential_uuid": "c9bf9e57-1685-4c89-bafb-ff5af830be8a"}),
            content_type=JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            self.url_path,
            data=json.dumps(
                {"credential_uuid": "c9bf9e57-1685-4c89-bafb-ff5af830be8a", "storage_id": "test-storage-id"}
            ),
            content_type=JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 404)


class IssueCredentialViewTestCase(SiteMixin, TestCase):
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
        )

    def authenticate_user(self, user):
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    @mock.patch("credentials.apps.verifiable_credentials.rest_api.v1.views.CredentialIssuer.issue")
    def test_post_valid_request(self, mock_issue):
        self.authenticate_user(self.user)
        mock_issue.return_value = {"verifiable_credential": "test"}

        url_path = reverse("verifiable_credentials:api:v1:credentials-issue", args=[str(self.issuance_line.uuid)])
        data = {"holder": "test-holder-id"}  # pylint: disable=redefined-outer-name
        response = self.client.post(url_path, json.dumps(data), JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"verifiable_credential": "test"})

    @mock.patch("credentials.apps.verifiable_credentials.rest_api.v1.views.CredentialIssuer.issue")
    def test_post_invalid_request_raises_validation_error(self, mock_issue):
        self.authenticate_user(self.user)
        mock_issue.side_effect = IssuanceException(detail="Invalid request.")
        data = {"holder": "test-holder-id"}  # pylint: disable=redefined-outer-name
        url_path = reverse("verifiable_credentials:api:v1:credentials-issue", args=[str(self.issuance_line.uuid)])
        response = self.client.post(url_path, json.dumps(data), JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AvailableStoragesViewTestCase(SiteMixin, TestCase):
    url_path = reverse("verifiable_credentials:api:v1:storages")

    def test_authentication(self):
        self.client.logout()
        response = self.client.get(self.url_path)
        self.assertEqual(response.status_code, 401)

        self.client.login(username=UserFactory().username, password=USER_PASSWORD)
        response = self.client.get(self.url_path)
        self.assertEqual(response.status_code, 200)

    @mock.patch("credentials.apps.verifiable_credentials.rest_api.v1.views.get_available_storages")
    def test_available_storages_view_returns_correct_data(self, mock_get_available_storages):
        self.client.logout()
        self.client.login(username=UserFactory().username, password=USER_PASSWORD)
        mock_get_available_storages.return_value = [LCWallet]
        response = self.client.get(self.url_path)
        self.assertEqual(response.data, [{"id": LCWallet.ID, "name": LCWallet.NAME}])


class StatusList2021ViewTestCase(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def authenticate_user(self, user):
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    @mock.patch("credentials.apps.verifiable_credentials.rest_api.v1.views.issue_status_list")
    @mock.patch("credentials.apps.verifiable_credentials.rest_api.v1.views.get_issuer_ids")
    def test_get_valid_request(self, mock_get_issuer_ids, mock_issue_status_list):
        self.authenticate_user(self.user)
        mock_get_issuer_ids.return_value = ["test-issuer-id"]
        mock_issue_status_list.return_value = {"test_status_list": "test"}

        url_path = reverse("verifiable_credentials:api:v1:status-list-2021-v1", args=["test-issuer-id"])
        response = self.client.get(url_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"test_status_list": "test"})
