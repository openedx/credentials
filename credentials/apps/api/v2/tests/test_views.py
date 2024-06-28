import datetime
import json
from decimal import Decimal
from unittest import mock

import ddt
import pytz
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APITestCase
from testfixtures import LogCapture
from waffle.testutils import override_switch

from credentials.apps.api.tests.mixins import JwtMixin
from credentials.apps.api.v2.serializers import (
    UserCredentialAttributeSerializer,
    UserCredentialSerializer,
    UserGradeSerializer,
)
from credentials.apps.api.v2.views import CredentialRateThrottle
from credentials.apps.catalog.tests.factories import CourseFactory, CourseRunFactory, ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialAttributeFactory,
    UserCredentialFactory,
)
from credentials.apps.records.models import UserGrade
from credentials.apps.records.tests.factories import UserGradeFactory


JSON_CONTENT_TYPE = "application/json"
LOGGER_NAME = "credentials.apps.credentials.issuers"
LOGGER_NAME_SERIALIZER = "credentials.apps.api.v2.serializers"


@ddt.ddt
class CredentialViewSetTests(SiteMixin, APITestCase):
    list_path = reverse("api:v2:credentials-list")

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def serialize_user_credential(self, user_credential, many=False):
        """Serialize the given UserCredential object(s)."""
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get("/")
        return UserCredentialSerializer(user_credential, context={"request": request}, many=many).data

    def authenticate_user(self, user):
        """Login as the given user."""
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def add_user_permission(self, user, permission):
        """Assigns a permission of the given name to the user."""
        user.user_permissions.add(Permission.objects.get(codename=permission))

    def assert_access_denied(self, user, method, path, data=None):
        """Asserts the given user cannot access the given path via the specified HTTP action/method."""
        self.client.login(username=user.username, password=USER_PASSWORD)
        if data:
            data = json.dumps(data)
        response = getattr(self.client, method)(path, data=data, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def test_authentication(self):
        """Verify the endpoint requires an authenticated user."""
        self.client.logout()
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 401)

        superuser = UserFactory(is_staff=True, is_superuser=True)
        self.authenticate_user(superuser)
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 200)

    def test_create(self):
        program = ProgramFactory(site=self.site)
        program_certificate = ProgramCertificateFactory(site=self.site, program_uuid=program.uuid, program=program)
        expected_username = self.user.username
        expected_attribute_name = "fake-name"
        expected_attribute_value = "fake-value"
        data = {
            "username": expected_username,
            "lms_user_id": 123,
            "credential": {"program_uuid": str(program_certificate.program_uuid)},
            "status": "awarded",
            "date_override": None,
            "attributes": [
                {
                    "name": expected_attribute_name,
                    "value": expected_attribute_value,
                }
            ],
        }

        # Verify users without the add permission are denied access
        self.assert_access_denied(self.user, "post", self.list_path, data=data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usercredential")
        response = self.client.post(self.list_path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        user_credential = UserCredential.objects.last()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_credential(user_credential))

        self.assertEqual(user_credential.username, expected_username)
        self.assertEqual(user_credential.credential, program_certificate)
        self.assertEqual(user_credential.attributes.count(), 1)

        attribute = user_credential.attributes.first()
        self.assertEqual(attribute.name, expected_attribute_name)
        self.assertEqual(attribute.value, expected_attribute_value)

    def test_create_with_duplicate_attributes(self):
        """Verify an error is returned if an attempt is made to create a UserCredential with multiple attributes
        of the same name."""
        program_certificate = ProgramCertificateFactory(site=self.site)
        data = {
            "username": "test-user",
            "lms_user_id": 123,
            "credential": {"program_uuid": str(program_certificate.program_uuid)},
            "attributes": [
                {
                    "name": "attr-name",
                    "value": "attr-value",
                },
                {
                    "name": "attr-name",
                    "value": "another-attr-value",
                },
            ],
        }

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usercredential")
        response = self.client.post(self.list_path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"attributes": ["Attribute names cannot be duplicated."]})

    def test_create_with_existing_user_credential(self):
        """Verify that, if a user has already been issued a credential, further attempts to issue the same credential
        will NOT create a new credential, but update the attributes of the existing credential.
        """
        user_credential = UserCredentialFactory(credential__site=self.site)
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usercredential")

        # POSTing the exact data that exists in the database should not change the UserCredential
        data = self.serialize_user_credential(user_credential)
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

        # POSTing with modified status/attributes should update the existing UserCredential
        data = self.serialize_user_credential(user_credential)
        expected_attribute = UserCredentialAttributeFactory.build()
        data["status"] = "revoked"
        data["attributes"] = [UserCredentialAttributeSerializer(expected_attribute).data]
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

        user_credential.refresh_from_db()
        self.assertEqual(response.data, self.serialize_user_credential(user_credential))
        self.assertEqual(user_credential.attributes.count(), 1)

        actual_attribute = user_credential.attributes.first()
        self.assertEqual(actual_attribute.name, expected_attribute.name)
        self.assertEqual(actual_attribute.value, expected_attribute.value)

    def test_create_with_date_override(self):
        """Verify that a UserCredentialDateOverride is created if a date_override
        is sent with the post"""

        course = CourseFactory.create(site=self.site)
        course_run = CourseRunFactory.create(course=course)

        expected_date_override = "9999-05-11T00:00:00Z"
        expected_attribute_name = "fake-name"
        expected_attribute_value = "fake-value"
        data = {
            "username": self.user.username,
            "lms_user_id": 123,
            "credential": {"course_run_key": course_run.key, "mode": "verified", "type": "course-run"},
            "status": "awarded",
            "date_override": {"date": expected_date_override},
            "attributes": [
                {
                    "name": expected_attribute_name,
                    "value": expected_attribute_value,
                }
            ],
        }

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usercredential")
        response = self.client.post(self.list_path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        user_credential = UserCredential.objects.last()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_credential(user_credential))

        self.assertEqual(user_credential.date_override.date.strftime("%Y-%m-%dT%H:%M:%SZ"), expected_date_override)

        # Verify that the date_override is removed if not present in the post
        data["date_override"] = None
        response = self.client.post(self.list_path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        user_credential.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            print(user_credential.date_override)

    def test_destroy(self):
        """Verify the endpoint does NOT support the DELETE operation."""
        credential = UserCredentialFactory(
            credential__site=self.site, status=UserCredential.AWARDED, username=self.user.username
        )
        path = reverse("api:v2:credentials-detail", kwargs={"uuid": credential.uuid})

        # Verify users without the view permission are denied access
        self.assert_access_denied(self.user, "delete", path)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "delete_usercredential")
        response = self.client.delete(path)
        credential.refresh_from_db()

        self.assertEqual(credential.status, UserCredential.REVOKED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.serialize_user_credential(credential))

    def test_retrieve(self):
        """Verify the endpoint returns data for a single UserCredential."""
        credential = UserCredentialFactory(credential__site=self.site, username=self.user.username)
        path = reverse("api:v2:credentials-detail", kwargs={"uuid": credential.uuid})

        # Verify users without the view permission are denied access
        self.assert_access_denied(self.user, "get", path)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.serialize_user_credential(credential))

    def test_list(self):
        """Verify the endpoint returns data for multiple UserCredentials."""
        # Verify users without the view permission are denied access
        self.assert_access_denied(self.user, "get", self.list_path)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["results"], self.serialize_user_credential(UserCredential.objects.all(), many=True)
        )

    def test_list_status_filtering(self):
        """Verify the endpoint returns data for all UserCredentials that match the specified status."""
        awarded = UserCredentialFactory.create_batch(3, credential__site=self.site, status=UserCredential.AWARDED)
        revoked = UserCredentialFactory.create_batch(3, credential__site=self.site, status=UserCredential.REVOKED)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")

        for status, expected in (("awarded", awarded), ("revoked", revoked)):
            response = self.client.get(self.list_path + f"?status={status}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["results"], self.serialize_user_credential(expected, many=True))

    def assert_list_username_filter_request_succeeds(self, username, expected):
        """Asserts the logged in user can list credentials for a specific user."""
        response = self.client.get(self.list_path + f"?username={username}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential(expected, many=True))

    def test_list_username_filtering(self):
        """Verify the endpoint returns data for all UserCredentials awarded to the user matching the username."""
        UserCredentialFactory.create_batch(3, credential__site=self.site)

        self.authenticate_user(self.user)

        # Users should be able to view their own credentials without additional permissions
        username = self.user.username
        expected = UserCredentialFactory.create_batch(3, credential__site=self.site, username=username)
        self.assert_list_username_filter_request_succeeds(username, expected)

        # Privileged users should be able to view all credentials
        username = "test_user"
        expected = UserCredentialFactory.create_batch(3, credential__site=self.site, username=username)
        self.add_user_permission(self.user, "view_usercredential")

        self.assert_list_username_filter_request_succeeds(username, expected)

    def test_invalid_program_uuid_filtering(self):
        """Verify that endpoint returns no results for invalid program uuid
        instead of raising ValidationError."""
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")

        response = self.client.get(self.list_path + "?program_uuid=1234fewef")
        self.assertListEqual(response.data["results"], [])

    def test_list_program_uuid_filtering(self):
        """Verify the endpoint returns data for all UserCredentials in the given program."""

        # Course run 1 is in a program, course run 2 is not
        course1_run = CourseRunFactory()
        course2_run = CourseRunFactory()
        program = ProgramFactory(course_runs=[course1_run])

        program_certificate = ProgramCertificateFactory(site=self.site, program_uuid=program.uuid)
        course1_certificate = CourseCertificateFactory(site=self.site, course_id=course1_run.key)
        course2_certificate = CourseCertificateFactory(site=self.site, course_id=course2_run.key)

        # Create some credentials related to the program
        course1_cred = UserCredentialFactory(credential=course1_certificate)
        program_creds = UserCredentialFactory.create_batch(3, credential=program_certificate)
        expected = [course1_cred] + program_creds

        # Create some more credentials that we don't expect to see returned
        UserCredentialFactory.create_batch(3)
        UserCredentialFactory(credential=course2_certificate)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")

        response = self.client.get(self.list_path + f"?program_uuid={program.uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential(expected, many=True))

    def test_list_type_filtering(self):
        """Verify the endpoint returns data for all UserCredentials for the given type."""
        program_certificate = ProgramCertificateFactory(site=self.site)
        course_run = CourseRunFactory()
        course_certificate = CourseCertificateFactory(course_id=course_run.key, course_run=course_run, site=self.site)

        course_cred = UserCredentialFactory(credential=course_certificate)
        program_cred = UserCredentialFactory(credential=program_certificate)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")

        response = self.client.get(self.list_path + "?type=course-run")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential([course_cred], many=True))

        response = self.client.get(self.list_path + "?type=program")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential([program_cred], many=True))

    def test_list_visible_filtering_with_certificate_available_date(self):
        """Verify the endpoint can filter by visible date."""
        course = CourseFactory.create(site=self.site)
        course_run = CourseRunFactory.create(course=course)
        course_certificate = CourseCertificateFactory.create(
            course_id=course_run.key, site=self.site, certificate_available_date="9999-05-11T03:14:01Z"
        )
        program = ProgramFactory(title="TestProgram1", course_runs=[course_run], site=self.site)
        program_certificate = ProgramCertificateFactory(site=self.site, program_uuid=program.uuid)
        program_certificate.program = program
        program_certificate.save()
        program_credential = UserCredentialFactory(username=self.user.username, credential=program_certificate)
        course_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential=course_certificate,
        )

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")

        both = [program_credential, course_credential]

        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential(both, many=True))

        response = self.client.get(self.list_path + "?only_visible=True")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential([], many=True))

        response = self.client.get(self.list_path + "?only_visible=False")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], self.serialize_user_credential(both, many=True))

    @ddt.data("put", "patch")
    def test_update(self, method):
        """Verify the endpoint supports updating the status of a UserCredential, but no other fields."""
        credential = UserCredentialFactory(credential__site=self.site, username=self.user.username)
        path = reverse("api:v2:credentials-detail", kwargs={"uuid": credential.uuid})
        expected_status = UserCredential.REVOKED
        data = {"status": expected_status}

        # Verify users without the change permission are denied access
        self.assert_access_denied(self.user, method, path, data=data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "change_usercredential")
        response = getattr(self.client, method)(path, data=data)
        credential.refresh_from_db()

        self.assertEqual(credential.status, expected_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.serialize_user_credential(credential))

    def test_site_filtering(self):
        """Verify the endpoint only returns credentials linked to a single site."""
        credential = UserCredentialFactory(credential__site=self.site)
        UserCredentialFactory()

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "view_usercredential")

        self.assertEqual(UserCredential.objects.count(), 2)

        response = self.client.get(self.list_path)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0], self.serialize_user_credential(credential))


@ddt.ddt
class GradeViewSetTests(SiteMixin, APITestCase):
    list_path = reverse("api:v2:grades-list")

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory(site=self.site)
        self.course_run = CourseRunFactory(course=self.course)
        self.data = {
            "username": "test_user",
            "course_run": self.course_run.key,
            "letter_grade": "A",
            "percent_grade": 0.9,
            "verified": True,
        }

    def serialize_user_grade(self, user_grade, many=False):
        """Serialize the given UserGrade object(s)."""
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get("/")
        return UserGradeSerializer(user_grade, context={"request": request}, many=many).data

    def authenticate_user(self, user):
        """Login as the given user."""
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def add_user_permission(self, user, permission):
        """Assigns a permission of the given name to the user."""
        user.user_permissions.add(Permission.objects.get(codename=permission))

    def assert_access_denied(self, user, method, path, data=None):
        """Asserts the given user cannot access the given path via the specified HTTP action/method."""
        self.client.login(username=user.username, password=USER_PASSWORD)
        if data:
            data = json.dumps(data)
        response = getattr(self.client, method)(path, data=data, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def test_authentication(self):
        """Verify the endpoint requires an authenticated user."""
        self.client.logout()
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

        superuser = UserFactory(is_staff=True, is_superuser=True)
        self.authenticate_user(superuser)
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

    def test_create(self):
        # Verify users without the add permission are denied access
        self.assert_access_denied(self.user, "post", self.list_path, data=self.data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usergrade")
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        grade = UserGrade.objects.last()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(grade))

        self.assertEqual(grade.username, self.data["username"])
        self.assertTrue(grade.verified)
        self.assertEqual(grade.letter_grade, self.data["letter_grade"])
        self.assertEqual(grade.percent_grade, Decimal("0.9"))
        self.assertEqual(grade.course_run, self.course_run)

    def test_create_with_empty_letter_grade(self):
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usergrade")

        # Empty value
        self.data["username"] = "empty"
        self.data["letter_grade"] = ""
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(UserGrade.objects.last()))

        # No value
        self.data["username"] = "noexist"
        del self.data["letter_grade"]
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(UserGrade.objects.last()))

        # Null value
        self.data["username"] = "null"
        self.data["letter_grade"] = None
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(UserGrade.objects.last()))

    def test_create_with_existing_user_grade(self):
        """Verify that, if a user has already been issued a grade, further attempts to issue the same grade
        will NOT create a new grade, but update the fields of the existing grade.
        """
        grade = UserGradeFactory(course_run=self.course_run)
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usergrade")

        # POSTing with modified data should update the existing UserGrade
        data = self.serialize_user_grade(grade)
        data["letter_grade"] = "B"
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

        grade.refresh_from_db()
        self.assertEqual(grade.letter_grade, "B")
        self.assertDictEqual(response.data, self.serialize_user_grade(grade))

    @ddt.data(True, False)
    def test_create_with_logging_decorator_enabled(self, decorator_enabled):
        """
        A test that verifies expected log messages from Grade views decorated with the `log_incoming_requests`
        decorator.
        """
        expected_log_decorator_enabled = (
            f"POST request received to endpoint [/api/v2/grades/] from user [{self.user.username}] originating from "
            f"[Unknown] with data: [{str.encode(json.dumps(self.data))}]"
        )
        formatted_grade = "{:.4f}".format(self.data["percent_grade"])
        expected_logs = [
            f"Updated grade for user [{self.data['username']}] in course [{self.data['course_run']}] with "
            f"percent_grade [{formatted_grade}], letter_grade [{self.data['letter_grade']}], verified "
            f"[{self.data['verified']}], and lms_last_updated_at [None]"
        ]

        if decorator_enabled:
            expected_logs.append(expected_log_decorator_enabled)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usergrade")

        with override_switch("api.log_incoming_requests", active=decorator_enabled):
            with LogCapture() as log:
                self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)

        log_messages = [log.msg for log in log.records]
        for log in expected_logs:
            assert log in log_messages

    @ddt.data("put", "patch")
    def test_update(self, method):
        """Verify the endpoint supports updating the status of a UserGrade, but no other fields."""
        grade = UserGradeFactory(
            course_run=self.course_run,
            username=self.user.username,
            letter_grade="C",
        )
        path = reverse("api:v2:grades-detail", kwargs={"pk": grade.id})

        # Verify users without the change permission are denied access
        self.assert_access_denied(self.user, method, path, data=self.data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "change_usergrade")
        response = getattr(self.client, method)(path, data=self.data)

        grade.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(grade.letter_grade, self.data["letter_grade"])
        self.assertDictEqual(response.data, self.serialize_user_grade(grade))

    def test_upgrade_with_lms_last_updated_at_data(self):
        """Verify the endpoint supports updating the status"""
        # create a grade record as it would be before we added the `lms_last_updated_at` field
        grade = UserGradeFactory(course_run=self.course_run)
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, "add_usergrade")

        # simulate updating the existing record with the new field in the data
        dt = datetime.datetime.now()
        last_updated_at = dt.replace(tzinfo=pytz.UTC)
        data = self.serialize_user_grade(grade)
        data["lms_last_updated_at"] = last_updated_at
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        # verify the data is part of the grade record as expected
        grade.refresh_from_db()
        self.assertEqual(grade.lms_last_updated_at, last_updated_at)


@ddt.ddt
class ThrottlingTests(TestCase):
    """Tests for CredentialRateThrottle."""

    def setUp(self):
        super().setUp()
        self.throttle = CredentialRateThrottle()

    @ddt.data("credential_view", "grade_view", "staff_override")
    def test_throttle_configuration(self, scope):
        """Verify that throttling is configured for each scope."""
        self.throttle.scope = scope
        self.assertIsNotNone(self.throttle.parse_rate(self.throttle.get_rate()))


@ddt.ddt
@mock.patch("django.conf.settings.USERNAME_REPLACEMENT_WORKER", "test_replace_username_service_worker")
class UsernameReplacementViewTests(JwtMixin, APITestCase):
    """Tests UsernameReplacementView"""

    SERVICE_USERNAME = "test_replace_username_service_worker"

    def setUp(self):
        super().setUp()
        self.service_user = UserFactory(username=self.SERVICE_USERNAME)
        self.url = reverse("api:v2:replace_usernames")

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
        return self.client.post(self.url, data, **headers, content_type=JSON_CONTENT_TYPE)

    def test_auth(self):
        """Verify the endpoint only works with the service worker"""
        data = {
            "username_mappings": [
                {"test_username_1": "test_new_username_1"},
                {"test_username_2": "test_new_username_2"},
            ]
        }

        # Test unauthenticated
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

        # Test non-service worker
        random_user = UserFactory()
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)

        # Test service worker
        response = self.call_api(self.service_user, data)
        self.assertEqual(response.status_code, 200)

    @ddt.data([{}, {}], {}, [{"test_key": "test_value", "test_key_2": "test_value_2"}])
    def test_bad_schema(self, mapping_data):
        """Verify the endpoint rejects bad data schema"""
        data = {"username_mappings": mapping_data}
        response = self.call_api(self.service_user, data)
        self.assertEqual(response.status_code, 400)

    def test_existing_and_non_existing_users(self):
        """
        Tests a mix of existing and non existing users. Users that don't exist
        in this service are also treated as a success because no work needs to
        be done changing their username.
        """
        random_users = [UserFactory() for _ in range(5)]
        fake_usernames = ["myname_" + str(x) for x in range(5)]
        existing_users = [{user.username: user.username + "_new"} for user in random_users]
        non_existing_users = [{username: username + "_new"} for username in fake_usernames]
        data = {"username_mappings": existing_users + non_existing_users}
        expected_response = {"failed_replacements": [], "successful_replacements": existing_users + non_existing_users}
        response = self.call_api(self.service_user, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)
