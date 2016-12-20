"""
Serializers for data manipulated by the credentials service APIs.
"""
import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from credentials.apps.api.accreditors import Accreditor
from credentials.apps.credentials.models import (
    CourseCertificate, ProgramCertificate,
    UserCredential, UserCredentialAttribute
)
from credentials.apps.credentials.utils import validate_duplicate_attributes

logger = logging.getLogger(__name__)


class CredentialField(serializers.Field):
    """ Field identifying the credential type and identifiers."""

    def to_internal_value(self, data):
        credential_id = None
        try:
            if 'program_id' in data and data.get('program_id'):
                credential_id = data['program_id']
                return ProgramCertificate.objects.get(program_id=credential_id, is_active=True)
            elif 'course_id' in data and data.get('course_id') and data.get('certificate_type'):
                credential_id = data['course_id']
                return CourseCertificate.objects.get(
                    course_id=credential_id,
                    certificate_type=data['certificate_type'],
                    is_active=True
                )
            else:
                raise ValidationError("Credential ID is missing.")
        except ObjectDoesNotExist as ex:
            logger.exception("Credential ID [%s] for %s", credential_id, ex.message)
            raise ValidationError(ex.message)

    def to_representation(self, value):
        """ Serialize objects to a according to model content-type. """
        credential = {
            'credential_id': value.id
        }
        if isinstance(value, ProgramCertificate):
            credential.update({
                'program_id': value.program_id,
            })
        elif isinstance(value, CourseCertificate):
            credential.update({
                'course_id': value.course_id,
                'certificate_type': value.certificate_type
            })

        return credential


class UserCertificateURLField(serializers.ReadOnlyField):  # pylint: disable=abstract-method
    """ Field for UserCredential URL pointing html view """

    def to_representation(self, value):
        """ Build the UserCredential URL for html view. Get the current domain from request. """
        return reverse(
            'credentials:render',
            kwargs={
                "uuid": value.hex,
            },
            request=self.context['request']
        )


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """ Serializer for CredentialAttribute objects """

    class Meta(object):
        model = UserCredentialAttribute
        fields = ('name', 'value')


class UserCredentialSerializer(serializers.ModelSerializer):
    """ Serializer for UserCredential objects. """

    credential = CredentialField(read_only=True)
    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)
    certificate_url = UserCertificateURLField(source='uuid')

    class Meta(object):
        model = UserCredential
        fields = (
            'id', 'username', 'credential', 'status', 'download_url', 'uuid', 'attributes', 'created', 'modified',
            'certificate_url',
        )
        read_only_fields = (
            'username', 'download_url', 'uuid', 'created', 'modified',
        )


class UserCredentialCreationSerializer(serializers.ModelSerializer):
    """ Serializer used to create UserCredential objects. """
    credential = CredentialField()
    attributes = UserCredentialAttributeSerializer(many=True)
    certificate_url = UserCertificateURLField(source='uuid')

    def validate_attributes(self, data):
        """ Check that the name attributes cannot be duplicated."""
        if not validate_duplicate_attributes(data):
            raise ValidationError("Attributes cannot be duplicated.")
        return data

    def issue_credential(self, validated_data):
        """
        Issue a new credential.

        Args:
            validated_data (dict): Input data specifying the credential type, recipient, and attributes.

        Returns:
            AbstractCredential
        """
        accreditor = Accreditor()
        credential = validated_data['credential']
        username = validated_data['username']
        attributes = validated_data.pop('attributes', None)

        return accreditor.issue_credential(credential, username, attributes)

    def create(self, validated_data):
        return self.issue_credential(validated_data)

    class Meta(object):
        model = UserCredential
        exclude = ('credential_content_type', 'credential_id')
