"""
Serializers for data manipulated by the credentials service APIs.
"""
import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from credentials.apps.api.accreditors import Accreditor
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.models import (CourseCertificate, ProgramCertificate, UserCredential,
                                                 UserCredentialAttribute)

logger = logging.getLogger(__name__)


class CredentialField(serializers.Field):
    """ Field identifying the credential type and identifiers."""

    def to_internal_value(self, data):
        site = self.context['request'].site

        program_uuid = data.get('program_uuid')
        if program_uuid:
            try:
                return ProgramCertificate.objects.get(program_uuid=program_uuid, is_active=True)
            except ObjectDoesNotExist:
                msg = 'No active ProgramCertificate exists for program [{}]'.format(program_uuid)
                logger.exception(msg)
                raise ValidationError({'program_uuid': msg})

        course_run_key = data.get('course_run_key')
        if course_run_key:
            if self.read_only:
                try:
                    cert = CourseCertificate.objects.get(course_id=course_run_key, site=site)
                except ObjectDoesNotExist:
                    cert = None
            else:
                # Create course cert on the fly, but don't upgrade it to active if it's manually been turned off
                cert, _ = CourseCertificate.objects.get_or_create(
                    course_id=course_run_key,
                    site=site,
                    defaults={
                        'is_active': True,
                        'certificate_type': data.get('mode'),
                    },
                )

            if cert is None or not cert.is_active:
                msg = 'No active CourseCertificate exists for course run [{}]'.format(course_run_key)
                logger.exception(msg)
                raise ValidationError({'course_run_key': msg})

            return cert

        raise ValidationError('Credential identifier is missing.')

    def to_representation(self, value):
        """ Serialize objects to a according to model content-type. """
        if hasattr(value, 'program_uuid'):
            credential = {
                'type': 'program',
                'credential_id': value.id,
                'program_uuid': value.program_uuid,
            }
        else:  # course run
            credential = {
                'type': 'course-run',
                'course_run_key': value.course_id,
                'mode': value.certificate_type,
            }

        return credential


class UserCertificateURLField(serializers.ReadOnlyField):  # pylint: disable=abstract-method
    """ Field for UserCredential URL pointing html view """

    def to_representation(self, value):
        """ Build the UserCredential URL for html view. Get the current domain from request. """
        return reverse(
            'credentials:render',
            kwargs={
                'uuid': value.hex,
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
    certificate_url = UserCertificateURLField(source='uuid', read_only=True)

    class Meta(object):
        model = UserCredential
        fields = (
            'username', 'credential', 'status', 'download_url', 'uuid', 'attributes', 'created', 'modified',
            'certificate_url',
        )
        read_only_fields = (
            'username', 'download_url', 'uuid', 'created', 'modified',
        )


class UserCredentialCreationSerializer(serializers.ModelSerializer):
    """ Serializer used to create UserCredential objects. """
    credential = CredentialField()
    attributes = UserCredentialAttributeSerializer(many=True, required=False)
    certificate_url = UserCertificateURLField(source='uuid')

    def validate_attributes(self, value):
        """ Check that the name attributes cannot be duplicated."""
        names = [attribute['name'] for attribute in value]

        if len(names) != len(set(names)):
            raise ValidationError('Attribute names cannot be duplicated.')

        return value

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
        status = validated_data.get('status', UserCredentialStatus.AWARDED)
        attributes = validated_data.pop('attributes', None)

        return accreditor.issue_credential(credential, username, status=status, attributes=attributes)

    def create(self, validated_data):
        return self.issue_credential(validated_data)

    class Meta(object):
        model = UserCredential
        fields = UserCredentialSerializer.Meta.fields
        read_only_fields = ('download_url', 'uuid', 'created', 'modified',)
