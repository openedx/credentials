from uuid import uuid4

import ddt
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory

from credentials.apps.api.v2.serializers import (
    CredentialField, UserCredentialAttributeSerializer, UserCredentialCreationSerializer, UserCredentialSerializer
)
from credentials.apps.credentials.tests.factories import (
    ProgramCertificateFactory, UserCredentialAttributeFactory, UserCredentialFactory
)


@ddt.ddt
class CredentialFieldTests(TestCase):
    def setUp(self):
        super(CredentialFieldTests, self).setUp()
        self.program_certificate = ProgramCertificateFactory()
        self.field_instance = CredentialField()

    def assert_program_uuid_validation_error_raised(self, program_uuid):
        try:
            self.field_instance.to_internal_value({'program_uuid': program_uuid})
        except ValidationError as ex:
            expected = {'program_uuid': 'No active ProgramCertificate exists for program [{}]'.format(program_uuid)}
            self.assertEqual(ex.detail, expected)

    def test_to_internal_value_with_empty_program_uuid(self):
        """ Verify an error is raised if no program UUID is provided. """

        with self.assertRaisesRegexp(ValidationError, 'Credential identifier is missing'):
            self.field_instance.to_internal_value({'program_uuid': ''})

    def test_to_internal_value_with_invalid_program_uuid(self, ):
        """ Verify the method raises a ValidationError if the passed program UUID does not correspond to a
        ProgramCertificate.
        """
        self.assert_program_uuid_validation_error_raised(uuid4())

    def test_to_internal_value_with_inactive_program_certificate(self, ):
        """ Verify the method raises a ValidationError if the ProgramCertificate is NOT active. """
        self.program_certificate.is_active = False
        self.program_certificate.save()
        self.assert_program_uuid_validation_error_raised(self.program_certificate.program_uuid)

    def test_to_internal_value_with_valid_program_credential(self):
        """ Verify the method returns the ProgramCertificate corresponding to the specified UUID. """

        self.assertEqual(
            self.field_instance.to_internal_value({'program_uuid': self.program_certificate.program_uuid}),
            self.program_certificate
        )

    def test_to_representation_data_with_program(self):
        """ Verify the method serializes the credential details to a dict. """

        expected = {
            'program_uuid': self.program_certificate.program_uuid,
            'credential_id': self.program_certificate.id
        }
        self.assertEqual(self.field_instance.to_representation(self.program_certificate), expected)


class UserCredentialAttributeSerializerTests(TestCase):
    def test_data(self):
        program_certificate = ProgramCertificateFactory()
        user_credential = UserCredentialFactory(credential=program_certificate)
        program_certificate_attr = UserCredentialAttributeFactory(user_credential=user_credential)

        expected = {
            'name': program_certificate_attr.name,
            'value': program_certificate_attr.value
        }
        actual = UserCredentialAttributeSerializer(program_certificate_attr).data
        self.assertEqual(actual, expected)


class UserCredentialCreationSerializerTests(TestCase):
    def test_data(self):
        """ Verify the serializer serializes a UserCredential exactly as UserCredentialSerializer does. """
        request = APIRequestFactory().get('/')
        user_credential = UserCredentialFactory()
        actual = UserCredentialCreationSerializer(user_credential, context={'request': request}).data
        expected = UserCredentialSerializer(user_credential, context={'request': request}).data
        self.assertEqual(actual, expected)

    def test_validate_attributes(self):
        """ Verify the method prevents attributes with duplicate names from being created. """
        serializer = UserCredentialCreationSerializer()

        value = []
        self.assertEqual(serializer.validate_attributes(value), value)

        value = [{'name': 'attr-name', 'value': 'attr-value'}]
        self.assertEqual(serializer.validate_attributes(value), value)

        with self.assertRaisesMessage(ValidationError, 'Attribute names cannot be duplicated.'):
            value = [{'name': 'attr-name', 'value': 'attr-value'}, {'name': 'attr-name', 'value': 'another-attr-value'}]
            serializer.validate_attributes(value)


class UserCredentialSerializerTests(TestCase):
    def test_data(self):
        request = APIRequestFactory().get('/')
        program_certificate = ProgramCertificateFactory()
        user_credential = UserCredentialFactory(credential=program_certificate)
        user_credential_attribute = UserCredentialAttributeFactory(user_credential=user_credential)

        expected_url = 'http://testserver{}'.format(
            reverse('credentials:render', kwargs={'uuid': user_credential.uuid.hex}))

        expected = {
            'username': user_credential.username,
            'uuid': str(user_credential.uuid),
            'credential': {
                'program_uuid': program_certificate.program_uuid,
                'credential_id': program_certificate.id,
            },
            'download_url': user_credential.download_url,
            'status': user_credential.status,
            'attributes': [
                {
                    'name': user_credential_attribute.name,
                    'value': user_credential_attribute.value
                }
            ],
            'created': user_credential.created.strftime(api_settings.DATETIME_FORMAT),
            'modified': user_credential.modified.strftime(api_settings.DATETIME_FORMAT),
            'certificate_url': expected_url
        }

        actual = UserCredentialSerializer(user_credential, context={'request': request}).data
        self.assertEqual(actual, expected)
