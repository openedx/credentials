import json
from unittest import mock

import ddt
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from credentials.apps.api.tests.mixins import JwtMixin
from credentials.apps.api.v2.serializers import UserCredentialSerializer
from credentials.apps.catalog.tests.factories import CourseRunFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import CourseCertificateFactory, UserCredentialFactory
from credentials.apps.records.utils import get_credentials


JSON_CONTENT_TYPE = "application/json"


@ddt.ddt
@mock.patch("django.conf.settings.LEARNER_STATUS_WORKER", "test_learner_status_service_worker")
class LearnerStatusViewTests(JwtMixin, SiteMixin, APITestCase):
    status_path = reverse("credentials_api:v1:learner_cert_status")

    SERVICE_USERNAME = "test_learner_status_service_worker"

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.SERVICE_USERNAME)

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    def authenticate_user(self, user):
        """Login as the given user."""
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def add_user_permission(self, user, permission):
        """Assigns a permission of the given name to the user."""
        user.user_permissions.add(Permission.objects.get(codename=permission))

    def serialize_user_credential(self, user_credential, many=False):
        """Serialize the given UserCredential object(s)."""
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get("/")
        return UserCredentialSerializer(user_credential, context={"request": request}, many=many).data

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        jwt_payload = self.default_payload(user)
        token = self.generate_token(jwt_payload)
        headers = {"HTTP_AUTHORIZATION": "JWT " + token}
        return headers

    def call_api(self, user, data):
        """Helper function to call API with data"""
        data = json.dumps(data)
        headers = self.build_jwt_headers(user)
        return self.client.post(self.status_path, data, **headers, content_type=JSON_CONTENT_TYPE)

    def create_credential(self, use_lms_id=False):
        course_run = CourseRunFactory.create()
        credential = CourseCertificateFactory.create(
            course_id=course_run.course.id, site=self.site, course_run=course_run
        )
        user_credential = UserCredentialFactory(
            credential=credential, credential__site=self.site, username=self.user.username
        )
        if use_lms_id:
            data = {
                "lms_user_id": self.user.lms_user_id,
                "courses": [str(user_credential.credential.course_run.course.uuid)],
            }
        else:
            data = {"username": self.user.username, "courses": [str(user_credential.credential.course_run.course.uuid)]}
        return user_credential, data

    def test_post(self):
        """
        Test with single course, no grade
        """
        course_run = CourseRunFactory.create()
        credential = CourseCertificateFactory.create(
            course_id=course_run.course.id, site=self.site, course_run=course_run
        )
        user_credential = UserCredentialFactory(
            credential=credential, credential__site=self.site, username=self.user.username
        )

        data = {"username": self.user.username, "courses": [str(course_run.course.uuid)]}

        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 200, msg="Did not get back expected response code")

        expected_data = {
            "lms_user_id": self.user.lms_user_id,
            "username": self.user.username,
            "status": [
                {
                    "course_uuid": str(course_run.course.uuid),
                    "course_run": {"uuid": str(course_run.uuid), "key": course_run.key},
                    "status": "awarded",
                    "type": "honor",
                    "certificate_available_date": None,
                    "grade": None,
                }
            ],
        }

        self.assertEqual(response.data, expected_data, msg="Unexpected value returned from query")

    def test_unknown_user(self):
        user_credential, data = self.create_credential()
        data["username"] = "unknown_user"
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 404)

    def test_unknown_lms_id(self):
        user_credential, data = self.create_credential(use_lms_id=True)
        data["lms_user_id"] = 999999
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 404)

    def test_lms_and_username(self):
        """Call should fail because only one of username or lms id can be provided."""
        user_credential, data = self.create_credential()
        data["lms_user_id"] = self.user.lms_user_id
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 400, msg="API should not allow lms_id AND username")

    def test_user_no_credentials(self):
        """Query for an existing course, but user has no credentials that match query"""
        """Generate credentials for the self user so there is a legit course"""
        user_credential, data = self.create_credential()
        uncredentialled_user = UserFactory()
        """slide in a different username with no courses"""
        data["username"] = uncredentialled_user.username
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], uncredentialled_user.username)
        self.assertEqual(len(response.data["status"]), 0)

    def test_auth(self):
        """Verify the endpoint does not works except with the service worker or admin"""
        user_credential, data = self.create_credential()

        # Test non-authenticated
        random_user = UserFactory()
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)

        self.authenticate_user(random_user)
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)
