""" Tests for Credit API serializers. """
from __future__ import unicode_literals

from django.test import TestCase

from credentials.apps.api import serializers
from credentials.apps.api.tests.factories import (
    CourseCertificateFactory, ProgramCertificateFactory,
    UserCredentialFactory, UserCredentialAttributeFactory
)
from credentials.apps.credentials.constants import DRF_DATE_FORMAT


class CredentialSerializerTests(TestCase):
    """ UserCredentialSerializer tests. """

    def setUp(self):
        super(CredentialSerializerTests, self).setUp()

        # create program cert
        self.program_cert = ProgramCertificateFactory.create(id=121, program_id=100)
        self.program_credential = UserCredentialFactory.create(credential=self.program_cert)
        self.program_cert_attr = UserCredentialAttributeFactory.create(user_credential=self.program_credential)

        # create course cert
        self.course_cert = CourseCertificateFactory.create()
        self.course_credential = UserCredentialFactory.create(credential=self.course_cert)
        self.course_cert_attr = UserCredentialAttributeFactory.create(user_credential=self.course_credential)

    def test_usercredentialserializer_for_program(self):
        """ Verify that UserCredentialSerializer serialize data correctly of program type."""
        serialize_data = serializers.UserCredentialSerializer(self.program_credential)
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
                    "namespace": self.program_cert_attr.namespace,
                    "name": self.program_cert_attr.name,
                    "value": self.program_cert_attr.value
                }
            ],
            "id": self.program_credential.id,
            "created": self.program_credential.created.strftime(DRF_DATE_FORMAT),
            "modified": self.program_credential.modified.strftime(DRF_DATE_FORMAT)
        }
        self.assertDictEqual(serialize_data.data, expected)

    def test_usercredentialserializer_for_course(self):
        """ Verify that UserCredentialSerializer serialize data correctly of course type."""

        serialize_data = serializers.UserCredentialSerializer(self.course_credential)
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
                    "namespace": self.course_cert_attr.namespace,
                    "name": self.course_cert_attr.name,
                    "value": self.course_cert_attr.value
                }
            ],
            "id": self.course_credential.id,
            "created": self.course_credential.created.strftime(DRF_DATE_FORMAT),
            "modified": self.course_credential.modified.strftime(DRF_DATE_FORMAT)
        }
        self.assertDictEqual(serialize_data.data, expected)

    def test_usercredentialattributeserializer(self):
        """ Verify that user CredentialAttributeSerializer serialize data correctly."""
        serialize_data = serializers.UserCredentialAttributeSerializer(self.program_cert_attr)
        expected = {
            "namespace": self.program_cert_attr.namespace,
            "name": self.program_cert_attr.name,
            "value": self.program_cert_attr.value
        }

        self.assertDictEqual(serialize_data.data, expected)

    def test_coursecertificateserializer(self):
        """ Verify that CourseCertificateSerializer serialize data correctly for
        course certificates.
        """
        serialize_data = serializers.CourseCertificateSerializer(self.course_cert)

        expected = {
            "user_credential": [
                {
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
                            "namespace": self.course_cert_attr.namespace,
                            "name": self.course_cert_attr.name,
                            "value": self.course_cert_attr.value
                        }
                    ],
                    "id": self.course_credential.id,
                    "created": self.course_credential.created.strftime(DRF_DATE_FORMAT),
                    "modified": self.course_credential.modified.strftime(DRF_DATE_FORMAT)
                }
            ],
            "course_id": self.course_cert.course_id,
            "certificate_type": self.course_cert.certificate_type
        }
        self.assertDictEqual(serialize_data.data, expected)

    def test_programcertificateserializer(self):
        """ Verify that ProgramCertificateSerializer serialize data correctly."""
        serialize_data = serializers.ProgramCertificateSerializer(self.program_cert)
        expected = {
            "program_id": self.program_cert.program_id,
            "user_credential": [
                {
                    "id": self.program_credential.id,
                    "username": self.program_credential.username,
                    "credential": {
                        "program_id": self.program_cert.program_id,
                        "credential_id": self.program_cert.id,
                    },
                    "status": self.program_credential.status,
                    "download_url": self.program_credential.download_url,
                    "uuid": str(self.program_credential.uuid),
                    "attributes": [
                        {
                            "namespace": self.program_cert_attr.namespace,
                            "name": self.program_cert_attr.name,
                            "value": self.program_cert_attr.value
                        }
                    ],
                    "created": self.program_credential.created.strftime(DRF_DATE_FORMAT),
                    "modified": self.program_credential.modified.strftime(DRF_DATE_FORMAT)
                }
            ]
        }
        self.assertDictEqual(serialize_data.data, expected)
