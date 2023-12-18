import json
from enum import Enum
from typing import TYPE_CHECKING
from unittest import mock

import ddt
from django.urls import reverse
from rest_framework.test import APITestCase

from credentials.apps.api.tests.mixins import JwtMixin
from credentials.apps.catalog.tests.factories import CourseRunFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import CourseCertificateFactory, UserCredentialFactory
from credentials.apps.records.tests.factories import UserGradeFactory


if TYPE_CHECKING:
    from credentials.apps.core.models import User
    from credentials.apps.credentials.models import CourseCertificate, CourseRun


JSON_CONTENT_TYPE = "application/json"
IdType = Enum("IdType", ["lms_user_id", "username"])
CredIdType = Enum("CredIdType", ["course_uuid", "course_run_uuid", "course_run_key"])
GradeType = Enum("GradeType", ["grade", "no_grade"])


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

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        Cloned and owned from elsewhere in the codebase, this should
        be part of a utility somewhere.
        """
        jwt_payload = self.default_payload(user)
        token = self.generate_token(jwt_payload)
        headers = {"HTTP_AUTHORIZATION": "JWT " + token}
        return headers

    def call_api(self, user, data):
        """
        Helper function to call API with data
        """
        data = json.dumps(data)
        headers = self.build_jwt_headers(user)
        return self.client.post(self.status_path, data, **headers, content_type=JSON_CONTENT_TYPE)

    def create_credential(
        self, id_type=IdType.username, cred_id_type=CredIdType.course_uuid, grade_type=GradeType.grade
    ):
        """
        Create the payload for a request and also the expected response.
        """
        course_run: "CourseRun" = CourseRunFactory.create()
        credential: "CourseCertificate" = CourseCertificateFactory.create(
            course_id=course_run.course.key, site=self.site, course_run=course_run
        )
        user_credential = UserCredentialFactory(
            credential=credential, credential__site=self.site, username=self.user.username
        )
        if grade_type == GradeType.grade:
            expected_grade = UserGradeFactory(username=self.user.username, course_run=course_run)

        data = {}
        if id_type == IdType.lms_user_id:
            data["lms_user_id"] = self.user.lms_user_id
        else:
            data["username"] = self.user.username

        if cred_id_type == CredIdType.course_run_uuid:
            data["course_runs"] = [str(user_credential.credential.course_run.uuid)]
        elif cred_id_type == CredIdType.course_run_key:
            data["course_runs"] = [str(user_credential.credential.course_run.key)]
        else:
            data["courses"] = [str(user_credential.credential.course_run.course.uuid)]

        expected_response = {
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

        if grade_type == GradeType.grade:
            expected_response["status"][0]["grade"] = {
                "letter_grade": expected_grade.letter_grade,
                "percent_grade": expected_grade.percent_grade,
                "verified": expected_grade.verified,
            }

        return data, expected_response

    @ddt.data(
        (IdType.lms_user_id, CredIdType.course_run_uuid, GradeType.grade),
        (IdType.lms_user_id, CredIdType.course_run_key, GradeType.no_grade),
        (IdType.username, CredIdType.course_uuid, GradeType.grade),
        (IdType.username, CredIdType.course_run_key, GradeType.grade),
    )
    @ddt.unpack
    def test_post_positive(self, id_type, cred_type, grade_type):
        """
        Test the iterations of id and course-run vs course
        """
        data, expected_response = self.create_credential(id_type, cred_type, grade_type)
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 200, msg="Did not get back expected response code")

        self.assertEqual(response.data, expected_response, msg="Unexpected value returned from query")

    @ddt.data(
        (IdType.lms_user_id, CredIdType.course_run_uuid, GradeType.grade),
        (IdType.username, CredIdType.course_run_uuid, GradeType.grade),
    )
    @ddt.unpack
    def test_unknown_user_returns_empty_status(self, id_type, cred_type, grade_type):
        """An unknown username or lms_user_id should return valid with an empty status.

        Uses the create_credential method, even though it's not really using the
        credential, in order to avoid replicating the logic of creating the data
        payload."""
        data, expected_response = self.create_credential(id_type, cred_type, grade_type)
        if id_type == IdType.lms_user_id:
            data["lms_user_id"] = 666
            data["username"] = None
        else:
            data["lms_user_id"] = None
            data["username"] = "i_am_a_big_faker"

        expected_response = {
            "lms_user_id": data["lms_user_id"],
            "username": data["username"],
            "status": [],
        }
        response = self.call_api(self.user, data)

        self.assertEqual(response.status_code, 200, msg="Did not get back expected response code")
        self.assertEqual(response.data, expected_response, msg="Unexpected value returned from query")

    def test_lms_and_username(self):
        """Call should fail because only one of username or lms id can be provided."""
        data, expected_response = self.create_credential()  # pylint: disable=unused-variable
        data["lms_user_id"] = self.user.lms_user_id
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 400, msg="API should not allow lms_id AND username")

    def test_user_no_credentials(self):
        """Query for an existing course, but user has no credentials that match query"""

        # Generate credentials for the self user so there is a legit course
        data, expected_response = self.create_credential()  # pylint: disable=unused-variable
        uncredentialled_user = UserFactory()
        # Slide in a different username with no courses
        data["username"] = uncredentialled_user.username
        response = self.call_api(self.user, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], uncredentialled_user.username)
        self.assertEqual(len(response.data["status"]), 0)

    def test_auth(self):
        """Verify the endpoint does not works except with the service worker or admin"""
        data, expected_response = self.create_credential()  # pylint: disable=unused-variable

        # Test non-authenticated
        random_user = UserFactory()
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)

        self.authenticate_user(random_user)
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)


@ddt.ddt
@mock.patch("django.conf.settings.LEARNER_STATUS_WORKER", "test_learner_status_service_worker")
class BulkLearnerStatusViewTests(JwtMixin, SiteMixin, APITestCase):
    status_path = reverse("credentials_api:v1:bulk_learner_cert_status")

    SERVICE_USERNAME = "test_learner_status_service_worker"

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory(username=self.SERVICE_USERNAME)
        self.user2 = UserFactory(username="test_user_2")

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    def authenticate_user(self, user):
        """Login as the given user."""
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        Cloned and owned from elsewhere in the codebase, this should
        be part of a utility somewhere.
        """
        jwt_payload = self.default_payload(user)
        token = self.generate_token(jwt_payload)
        headers = {"HTTP_AUTHORIZATION": "JWT " + token}
        return headers

    def call_api(self, user, data):
        """
        Helper function to call API with data
        """
        data = json.dumps(data)
        headers = self.build_jwt_headers(user)
        return self.client.post(self.status_path, data, **headers, content_type=JSON_CONTENT_TYPE)

    def create_test_data(
        self,
        user: "User",
        id_type: str = IdType.username,
        cred_id_type: str = CredIdType.course_uuid,
        grade_type: str = GradeType.grade,
    ):
        """
        Create the payload for a request (user, course run, cred) and also the expected response.
        """
        course_run: "CourseRun" = CourseRunFactory.create()
        credential: "CourseCertificate" = CourseCertificateFactory.create(
            course_id=course_run.course.key, site=self.site, course_run=course_run
        )
        user_credential = UserCredentialFactory(
            credential=credential, credential__site=self.site, username=user.username
        )
        if grade_type == GradeType.grade:
            expected_grade = UserGradeFactory(username=user.username, course_run=course_run)

        data = {}
        if id_type == IdType.lms_user_id:
            data["lms_user_id"] = user.lms_user_id
        else:
            data["username"] = user.username

        if cred_id_type == CredIdType.course_run_uuid:
            data["course_runs"] = [str(user_credential.credential.course_run.uuid)]
        elif cred_id_type == CredIdType.course_run_key:
            data["course_runs"] = [str(user_credential.credential.course_run.key)]
        else:
            data["courses"] = [str(user_credential.credential.course_run.course.uuid)]

        expected_response = {
            "lms_user_id": user.lms_user_id,
            "username": user.username,
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

        if grade_type == GradeType.grade:
            expected_response["status"][0]["grade"] = {
                "letter_grade": expected_grade.letter_grade,
                "percent_grade": expected_grade.percent_grade,
                "verified": expected_grade.verified,
            }

        return data, expected_response

    @ddt.data(
        (IdType.lms_user_id, CredIdType.course_run_uuid, GradeType.grade),
        (IdType.lms_user_id, CredIdType.course_run_key, GradeType.no_grade),
        (IdType.username, CredIdType.course_uuid, GradeType.grade),
        (IdType.username, CredIdType.course_run_key, GradeType.grade),
    )
    @ddt.unpack
    def test_post_positive(self, id_type, cred_type, grade_type):
        """
        Test the iterations of id and course-run vs course
        """
        data1, expected_response1 = self.create_test_data(self.user1, id_type, cred_type, grade_type)
        data2, expected_response2 = self.create_test_data(self.user2, id_type, cred_type, grade_type)
        data = [data1, data2]
        expected_response = [expected_response1, expected_response2]

        response = self.call_api(self.user1, data)
        self.assertEqual(response.status_code, 200, msg="Did not get back expected response code")

        self.assertEqual(response.data, expected_response, msg="Unexpected value returned from query")

    @ddt.data(
        (IdType.lms_user_id, CredIdType.course_run_uuid, GradeType.grade),
        (IdType.username, CredIdType.course_run_uuid, GradeType.grade),
    )
    @ddt.unpack
    def test_unknown_user_returns_empty_status(self, id_type, cred_type, grade_type):
        """An unknown username or lms_user_id should return valid with an empty status.

        Uses the create_test_data method, even though it's not really using the
        credential, in order to avoid replicating the logic of creating the data
        payload."""
        data1, expected_response1 = self.create_test_data(self.user1, id_type, cred_type, grade_type)
        data2, expected_response2 = self.create_test_data(self.user2, id_type, cred_type, grade_type)
        if id_type == IdType.lms_user_id:
            data1["lms_user_id"] = 666
            data1["username"] = None
        else:
            data1["lms_user_id"] = None
            data1["username"] = "i_am_a_big_faker"

        expected_response1 = {
            "lms_user_id": data1["lms_user_id"],
            "username": data1["username"],
            "status": [],
        }

        data = [data1, data2]
        expected_response = [expected_response1, expected_response2]

        response = self.call_api(self.user1, data)

        self.assertEqual(response.status_code, 200, msg="Did not get back expected response code")
        self.assertEqual(response.data, expected_response, msg="Unexpected value returned from query")

    def test_lms_and_username(self):
        """Call should fail because only one of username or lms id can be provided."""
        data1, expected_response1 = self.create_test_data(self.user1)  # pylint: disable=unused-variable
        data2, expected_response2 = self.create_test_data(self.user2)  # pylint: disable=unused-variable
        data1["lms_user_id"] = self.user1.lms_user_id
        data = [data1, data2]

        response = self.call_api(self.user1, data)
        self.assertEqual(response.status_code, 400, msg="API should not allow lms_id AND username")

    def test_user_no_credentials(self):
        """Query for an existing course, but user has no credentials that match query"""

        # Generate credentials, including one for the login user, so there is a legit course
        data1, expected_response1 = self.create_test_data(self.user1)  # pylint: disable=unused-variable
        data2, expected_response2 = self.create_test_data(self.user2)  # pylint: disable=unused-variable

        # Slide in a different username with no courses
        uncredentialled_user = UserFactory()
        data1["username"] = uncredentialled_user.username

        data = [data1, data2]

        response = self.call_api(self.user1, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["username"], uncredentialled_user.username)
        self.assertEqual(len(response.data[0]["status"]), 0)

    def test_auth(self):
        """Verify the endpoint does not work except with the service worker or admin"""
        data1, expected_response1 = self.create_test_data(self.user1)  # pylint: disable=unused-variable
        data2, expected_response2 = self.create_test_data(self.user2)  # pylint: disable=unused-variable

        data = [data1, data2]

        # Test non-authenticated
        random_user = UserFactory()
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)

        self.authenticate_user(random_user)
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)
