from collections import namedtuple
from datetime import datetime
from logging import WARNING
from uuid import uuid4
from zoneinfo import ZoneInfo

import ddt
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory

from credentials.apps.api.v2.serializers import (
    CourseCertificateSerializer,
    CredentialField,
    UserCredentialAttributeSerializer,
    UserCredentialCreationSerializer,
    UserCredentialSerializer,
    UserGradeSerializer,
)
from credentials.apps.catalog.tests.factories import CourseFactory, CourseRunFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.models import CourseCertificate
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialAttributeFactory,
    UserCredentialFactory,
)
from credentials.apps.records.tests.factories import UserGradeFactory


@ddt.ddt
class CredentialFieldTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.program_certificate = ProgramCertificateFactory(site=self.site)
        self.course_run = CourseRunFactory()
        self.course_certificate = CourseCertificateFactory(
            site=self.site,
            certificate_type="verified",
            course_run=self.course_run,
            course_id=self.course_run.key,
        )
        self.field_instance = CredentialField()
        # see: https://github.com/encode/django-rest-framework/blob/3.9.x/rest_framework/fields.py#L610
        # pylint: disable=protected-access
        self.field_instance._context = {
            "request": namedtuple("HttpRequest", ["site"])(self.site),
        }

    def assert_program_uuid_validation_error_raised(self, program_uuid):
        try:
            self.field_instance.to_internal_value({"program_uuid": program_uuid})
        except ValidationError as ex:
            expected = {"program_uuid": f"No active ProgramCertificate exists for program [{program_uuid}]"}
            self.assertEqual(ex.detail, expected)

    def assert_course_run_key_validation_error_raised(self, course_run_key):
        try:
            self.field_instance.to_internal_value({"course_run_key": course_run_key, "mode": "verified"})
        except ValidationError as ex:
            expected = {"course_run_key": f"No active CourseCertificate exists for course run [{course_run_key}]"}
            self.assertEqual(ex.detail, expected)

    def assert_course_run_key_creation_validation_error_raised(self, course_run_key):
        try:
            self.field_instance.to_internal_value({"course_run_key": course_run_key, "mode": "verified"})
        except ValidationError as ex:
            expected = {
                "course_run_key": (
                    f"CourseCertificate failed to create because the CourseRun {course_run_key} doesn't exist in the "
                    "catalog"
                )
            }
            self.assertEqual(ex.detail, expected)

    def test_to_internal_value_with_empty_program_uuid(self):
        """Verify an error is raised if no program UUID is provided."""

        with self.assertRaisesMessage(ValidationError, "Credential identifier is missing"):
            self.field_instance.to_internal_value({"program_uuid": ""})

    def test_to_internal_value_with_invalid_program_uuid(
        self,
    ):
        """Verify the method raises a ValidationError if the passed program UUID does not correspond to a
        ProgramCertificate.
        """
        self.assert_program_uuid_validation_error_raised(uuid4())

    def test_to_internal_value_with_invalid_site(
        self,
    ):
        """Verify the method raises a ValidationError if the passed program UUID belongs to a different site."""
        certificate = ProgramCertificateFactory()  # without setting site=self.site
        self.assert_program_uuid_validation_error_raised(certificate.program_uuid)

    def test_to_internal_value_with_inactive_program_certificate(
        self,
    ):
        """Verify the method raises a ValidationError if the ProgramCertificate is NOT active."""
        self.program_certificate.is_active = False
        self.program_certificate.save()
        self.assert_program_uuid_validation_error_raised(self.program_certificate.program_uuid)

    def test_to_internal_value_with_valid_program_credential(self):
        """Verify the method returns the ProgramCertificate corresponding to the specified UUID."""

        self.assertEqual(
            self.field_instance.to_internal_value({"program_uuid": self.program_certificate.program_uuid}),
            self.program_certificate,
        )

    def test_to_internal_value_with_created_course_credential(self):
        """Verify the method creates a course credential if needed."""
        course_run = CourseRunFactory()
        credential = self.field_instance.to_internal_value({"course_run_key": course_run.key, "mode": "verified"})
        self.assertEqual(credential, CourseCertificate.objects.get(course_id=course_run.key))

    def test_to_internal_value_with_missing_course_run(self):
        """Verify the method raises an error if the course run is missing."""
        self.assert_course_run_key_creation_validation_error_raised("fake-run")

    def test_to_internal_value_with_present_course_credential_read_only(self):
        """Verify the method finds a course credential when read-only."""
        self.field_instance.read_only = True
        self.assertEqual(
            self.field_instance.to_internal_value({"course_run_key": self.course_run.key, "mode": "verified"}),
            self.course_certificate,
        )

        self.assert_course_run_key_validation_error_raised("create-me")

    def test_to_internal_value_with_created_course_credential_read_only(self):
        """Verify the method refuses to create a course credential when read-only."""
        self.field_instance.read_only = True
        self.assert_course_run_key_validation_error_raised("create-me")

    def test_to_internal_value_with_created_course_credential_no_type_change(self):
        """Verify the method won't update cert information when creating a course credential."""
        credential = self.field_instance.to_internal_value(
            {"course_run_key": self.course_certificate.course_id, "mode": "honor"}
        )
        credential.refresh_from_db()  # just in case
        self.assertEqual(credential.certificate_type, "verified")

    def test_to_internal_value_with_inactive_course_credential(self):
        """Verify the method raises a ValidationError if the CourseCertificate is NOT active."""
        self.course_certificate.is_active = False
        self.course_certificate.save()
        self.assert_course_run_key_validation_error_raised(self.course_certificate.course_id)

    def test_to_internal_value_with_valid_course_credential(self):
        """Verify the method serializes the course credential details to a dict."""
        self.assertEqual(
            self.field_instance.to_internal_value(
                {"course_run_key": self.course_certificate.course_id, "mode": "verified"}
            ),
            self.course_certificate,
        )

    def test_to_representation_data_with_program(self):
        """Verify the method serializes the credential details to a dict."""

        expected = {
            "type": "program",
            "program_uuid": self.program_certificate.program_uuid,
            "credential_id": self.program_certificate.id,
        }
        self.assertEqual(self.field_instance.to_representation(self.program_certificate), expected)

    def test_to_representation_data_with_course(self):
        """Verify the method serializes the credential details to a dict."""

        expected = {
            "type": "course-run",
            "course_run_key": self.course_certificate.course_id,
            "mode": self.course_certificate.certificate_type,
        }
        self.assertEqual(self.field_instance.to_representation(self.course_certificate), expected)


class UserGradeSerializerTests(SiteMixin, TestCase):
    def test_to_representation(self):
        grade = UserGradeFactory()

        expected = {
            "id": grade.id,
            "username": grade.username,
            "course_run": grade.course_run.key,
            "letter_grade": grade.letter_grade,
            "percent_grade": str(grade.percent_grade),
            "verified": grade.verified,
            "lms_last_updated_at": None,
            "created": grade.created.strftime(api_settings.DATETIME_FORMAT),
            "modified": grade.modified.strftime(api_settings.DATETIME_FORMAT),
        }
        actual = UserGradeSerializer(grade).data
        self.assertDictEqual(actual, expected)

    def test_to_internal_value(self):
        Request = namedtuple("Request", ["site"])
        serializer = UserGradeSerializer(context={"request": Request(site=self.site)})
        updated_at_dt = datetime.now()
        updated_at_utc = updated_at_dt.replace(tzinfo=ZoneInfo("UTC"))

        data = {
            "username": "alice",
            "course_run": "nope",
            "letter_grade": "A",
            "percent_grade": 0.9,
            "verified": True,
            "lms_last_updated_at": updated_at_utc,
        }

        with self.assertRaisesMessage(ValidationError, "No CourseRun exists for key [nope]"):
            serializer.to_internal_value(data)

        course = CourseFactory(site=self.site)
        course_run = CourseRunFactory(course=course)
        data["course_run"] = course_run.key

        grade = serializer.to_internal_value(data)
        self.assertEqual(grade["username"], "alice")
        self.assertEqual(grade["course_run"], course_run)
        self.assertEqual(grade["verified"], True)
        self.assertEqual(grade["letter_grade"], "A")
        self.assertEqual(str(grade["percent_grade"]), "0.9000")
        self.assertEqual(grade["lms_last_updated_at"], updated_at_utc)


class UserCredentialAttributeSerializerTests(TestCase):
    def test_data(self):
        program_certificate = ProgramCertificateFactory()
        user_credential = UserCredentialFactory(credential=program_certificate)
        program_certificate_attr = UserCredentialAttributeFactory(user_credential=user_credential)

        expected = {"name": program_certificate_attr.name, "value": program_certificate_attr.value}
        actual = UserCredentialAttributeSerializer(program_certificate_attr).data
        self.assertEqual(actual, expected)


class UserCredentialCreationSerializerTests(TestCase):
    def test_data(self):
        """Verify the serializer serializes a UserCredential exactly as UserCredentialSerializer does."""
        request = APIRequestFactory().get("/")
        user_credential = UserCredentialFactory()
        actual = UserCredentialCreationSerializer(user_credential, context={"request": request}).data
        expected = UserCredentialSerializer(user_credential, context={"request": request}).data
        self.assertEqual(actual, expected)

    def test_validate_attributes(self):
        """Verify the method prevents attributes with duplicate names from being created."""
        serializer = UserCredentialCreationSerializer()

        value = []
        self.assertEqual(serializer.validate_attributes(value), value)

        value = [{"name": "attr-name", "value": "attr-value"}]
        self.assertEqual(serializer.validate_attributes(value), value)

        with self.assertRaisesMessage(ValidationError, "Attribute names cannot be duplicated."):
            value = [{"name": "attr-name", "value": "attr-value"}, {"name": "attr-name", "value": "another-attr-value"}]
            serializer.validate_attributes(value)


class UserCredentialSerializerTests(TestCase):
    def test_program_credential(self):
        request = APIRequestFactory().get("/")
        program_certificate = ProgramCertificateFactory()
        user_credential = UserCredentialFactory(credential=program_certificate)
        user_credential_attribute = UserCredentialAttributeFactory(user_credential=user_credential)

        expected_url = "http://testserver{}".format(
            reverse("credentials:render", kwargs={"uuid": user_credential.uuid.hex})
        )

        expected = {
            "username": user_credential.username,
            "uuid": str(user_credential.uuid),
            "credential": {
                "type": "program",
                "program_uuid": program_certificate.program_uuid,
                "credential_id": program_certificate.id,
            },
            "date_override": None,
            "status": user_credential.status,
            "attributes": [{"name": user_credential_attribute.name, "value": user_credential_attribute.value}],
            "created": user_credential.created.strftime(api_settings.DATETIME_FORMAT),
            "modified": user_credential.modified.strftime(api_settings.DATETIME_FORMAT),
            "certificate_url": expected_url,
        }

        actual = UserCredentialSerializer(user_credential, context={"request": request}).data
        self.assertEqual(actual, expected)

    def test_course_credential(self):
        request = APIRequestFactory().get("/")
        course_run = CourseRunFactory()
        course_certificate = CourseCertificateFactory(
            certificate_type="verified",
            course_run=course_run,
            course_id=course_run.key,
        )
        user_credential = UserCredentialFactory(credential=course_certificate)
        user_credential_attribute = UserCredentialAttributeFactory(user_credential=user_credential)

        expected_url = "http://testserver{}".format(
            reverse("credentials:render", kwargs={"uuid": user_credential.uuid.hex})
        )

        expected = {
            "username": user_credential.username,
            "uuid": str(user_credential.uuid),
            "credential": {
                "type": "course-run",
                "course_run_key": course_certificate.course_id,
                "mode": course_certificate.certificate_type,
            },
            "date_override": None,
            "status": user_credential.status,
            "attributes": [{"name": user_credential_attribute.name, "value": user_credential_attribute.value}],
            "created": user_credential.created.strftime(api_settings.DATETIME_FORMAT),
            "modified": user_credential.modified.strftime(api_settings.DATETIME_FORMAT),
            "certificate_url": expected_url,
        }

        actual = UserCredentialSerializer(user_credential, context={"request": request}).data
        self.assertEqual(actual, expected)


class CourseCertificateSerializerTests(SiteMixin, TestCase):
    def test_create_course_certificate(self):
        """We can create a course certificate configuration"""
        course_run = CourseRunFactory()
        course_certificate = CourseCertificateFactory(site=self.site, course_run=course_run)
        Request = namedtuple("Request", ["site"])
        actual = CourseCertificateSerializer(course_certificate, context={"request": Request(site=self.site)}).data
        expected = {
            "id": course_certificate.id,
            "site": self.site.id,
            "course_id": course_certificate.course_id,
            "course_run": course_certificate.course_run.key,
            "certificate_type": course_certificate.certificate_type,
            "certificate_available_date": course_certificate.certificate_available_date,
            "is_active": course_certificate.is_active,
        }
        self.assertEqual(actual, expected)

    def test_missing_course_run(self):
        """We can create a course certificate configuration without a course run"""
        course_certificate = CourseCertificateFactory(site=self.site, course_run=None)
        Request = namedtuple("Request", ["site"])
        actual = CourseCertificateSerializer(course_certificate, context={"request": Request(site=self.site)}).data
        expected = {
            "id": course_certificate.id,
            "site": self.site.id,
            "course_run": None,
            "course_id": course_certificate.course_id,
            "certificate_type": course_certificate.certificate_type,
            "certificate_available_date": course_certificate.certificate_available_date,
            "is_active": course_certificate.is_active,
        }
        self.assertEqual(actual, expected)

    def test_create_without_course_run_raises_warning(self):
        """Creating a course certificate configuration without a course run raises a warning"""
        with self.assertLogs(level=WARNING):
            Request = namedtuple("Request", ["site"])
            CourseCertificateSerializer(context={"request": Request(site=self.site)}).create(
                validated_data={
                    "course_id": "DemoCourse0",
                    "certificate_type": "verified",
                    "is_active": True,
                    "certificate_available_date": None,
                }
            )

    def test_missing_certificate_available_date(self):
        """We can create a course certificate configuration without a certificate available date"""
        course_run = CourseRunFactory()
        course_certificate = CourseCertificateFactory(
            site=self.site,
            course_run=course_run,
            certificate_available_date=None,
        )
        Request = namedtuple("Request", ["site"])
        actual = CourseCertificateSerializer(course_certificate, context={"request": Request(site=self.site)}).data
        expected = {
            "id": course_certificate.id,
            "site": self.site.id,
            "course_run": course_certificate.course_run.key,
            "course_id": course_certificate.course_id,
            "certificate_type": course_certificate.certificate_type,
            "certificate_available_date": None,
            "is_active": course_certificate.is_active,
        }
        self.assertEqual(actual, expected)
