""" Tests for Credit API serializers. """
# pylint: disable=no-member
from __future__ import unicode_literals
import ddt
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory

from credentials.apps.api import serializers
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory, ProgramCertificateFactory, UserCredentialFactory, UserCredentialAttributeFactory
)


class UserCredentialSerializerTests(TestCase):
    """ UserCredentialSerializer tests. """

    def setUp(self):
        super(UserCredentialSerializerTests, self).setUp()

        self.program_cert = ProgramCertificateFactory()
        self.program_credential = UserCredentialFactory(credential=self.program_cert)
        self.program_cert_attr = UserCredentialAttributeFactory(user_credential=self.program_credential)

        self.course_cert = CourseCertificateFactory.create()
        self.course_credential = UserCredentialFactory.create(credential=self.course_cert)
        self.course_cert_attr = UserCredentialAttributeFactory(user_credential=self.course_credential)
        self.request = APIRequestFactory().get('/')

    def test_serialization_with_program_credential(self):
        """ Verify the serializer correctly serializes program credentials."""

        actual = serializers.UserCredentialSerializer(self.program_credential, context={
            "request": self.request
        }).data

        expected_url = "http://testserver{}".format(reverse("credentials:render", kwargs={
            "uuid": self.program_credential.uuid.hex,
        }))

        expected = {
            "username": self.program_credential.username,
            "uuid": str(self.program_credential.uuid),
            "credential": {
                "program_id": self.program_cert.program_id,
                "credential_id": self.program_cert.id,
            },
            "download_url": self.program_credential.download_url,
            "status": self.program_credential.status,
            "attributes": [
                {
                    "name": self.program_cert_attr.name,
                    "value": self.program_cert_attr.value
                }
            ],
            "id": self.program_credential.id,
            "created": self.program_credential.created.strftime(api_settings.DATETIME_FORMAT),
            "modified": self.program_credential.modified.strftime(api_settings.DATETIME_FORMAT),
            "certificate_url": expected_url
        }
        self.assertEqual(actual, expected)

    def test_serialization_with_course_credential(self):
        """ Verify the serializer correctly serializes course credentials."""

        actual = serializers.UserCredentialSerializer(self.course_credential, context={
            "request": self.request
        }).data

        expected_url = "http://testserver{}".format(reverse("credentials:render", kwargs={
            "uuid": self.course_credential.uuid.hex,
        }))

        expected = {
            "username": self.course_credential.username,
            "uuid": str(self.course_credential.uuid),
            "credential": {
                "course_id": self.course_cert.course_id,
                "certificate_type": self.course_cert.certificate_type,
                "credential_id": self.course_cert.id
            },
            "download_url": self.course_credential.download_url,
            "status": self.course_credential.status,
            "attributes": [
                {
                    "name": self.course_cert_attr.name,
                    "value": self.course_cert_attr.value
                }
            ],
            "id": self.course_credential.id,
            "created": self.course_credential.created.strftime(api_settings.DATETIME_FORMAT),
            "modified": self.course_credential.modified.strftime(api_settings.DATETIME_FORMAT),
            "certificate_url": expected_url,
        }
        self.assertEqual(actual, expected)


class UserCredentialAttributeSerializerTests(TestCase):
    """ CredentialAttributeSerializer tests. """

    def setUp(self):
        super(UserCredentialAttributeSerializerTests, self).setUp()
        self.program_cert = ProgramCertificateFactory()
        self.program_credential = UserCredentialFactory(credential=self.program_cert)
        self.program_cert_attr = UserCredentialAttributeFactory(user_credential=self.program_credential)

    def test_data(self):
        """ Verify that user CredentialAttributeSerializer serialize data correctly."""
        serialize_data = serializers.UserCredentialAttributeSerializer(self.program_cert_attr)
        expected = {
            "name": self.program_cert_attr.name,
            "value": self.program_cert_attr.value
        }

        self.assertEqual(serialize_data.data, expected)


@ddt.ddt
class CredentialFieldTests(TestCase):
    """ CredentialField tests. """

    def setUp(self):
        super(CredentialFieldTests, self).setUp()
        self.program_cert = ProgramCertificateFactory()
        self.field_instance = serializers.CredentialField()

    @ddt.data(
        {"program_id": ""},
        {"course_id": ""},
        {"course_id": 404, 'certificate_type': ''},
    )
    def test_to_internal_value_with_empty_credential(self, credential_data):
        """Verify that it will return error message if credential-id attributes are empty."""

        with self.assertRaisesRegexp(ValidationError, "Credential ID is missing"):
            self.field_instance.to_internal_value(credential_data)

    def test_to_internal_value_with_invalid_program_credential(self,):
        """Verify that it will return error message if program-id does not exist in db."""

        with self.assertRaisesRegexp(ValidationError, "ProgramCertificate matching query does not exist."):
            self.field_instance.to_internal_value({"program_id": 404})

    def test_to_internal_value_with_in_active_program_credential(self,):
        """Verify that it will return error message if program is not active in db."""
        self.program_cert.is_active = False
        self.program_cert.save()

        with self.assertRaisesRegexp(ValidationError, "ProgramCertificate matching query does not exist."):
            self.field_instance.to_internal_value({"program_id": 404})

    def test_to_internal_value_with_invalid_course_credential(self):
        """Verify that it will return error message if course-id does not exist in db."""

        with self.assertRaisesRegexp(ValidationError, "CourseCertificate matching query does not exist."):
            self.field_instance.to_internal_value({"course_id": 404, 'certificate_type': "honor"})

    def test_to_internal_value_with_valid_program_credential(self):
        """Verify that it will return credential object if program-id found in db."""

        self.assertEqual(
            self.program_cert,
            self.field_instance.to_internal_value({"program_id": self.program_cert.program_id})
        )

    def test_to_internal_value_with_valid_course_credential(self):
        """Verify that it will return credential object if course-id and certificate type
        found in db."""

        course_cert = CourseCertificateFactory()
        self.assertEqual(
            course_cert,
            self.field_instance.to_internal_value({"course_id": course_cert.course_id, "certificate_type": "honor"})
        )

    def test_to_representation_data_with_program(self):
        """Verify that it will return program certificate credential object in dict format."""

        expected_data = {"program_id": self.program_cert.program_id, "credential_id": self.program_cert.id}
        self.assertEqual(
            expected_data,
            self.field_instance.to_representation(
                self.program_cert
            )
        )

    def test_to_representation_with_course(self):
        """Verify that it will return course certificate credential object in dict format."""

        course_cert = CourseCertificateFactory()
        expected_data = {
            "course_id": course_cert.course_id,
            "credential_id": course_cert.id,
            "certificate_type": course_cert.certificate_type
        }
        self.assertEqual(
            expected_data,
            self.field_instance.to_representation(
                course_cert
            )
        )
