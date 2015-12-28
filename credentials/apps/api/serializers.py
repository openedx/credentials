"""
Serializers for data manipulated by the credentials service APIs.
"""
from rest_framework import serializers

from credentials.apps.credentials.models import (
    CourseCertificate, ProgramCertificate,
    UserCredential, UserCredentialAttribute
)


class CredentialRelatedField(serializers.RelatedField):  # pylint: disable=abstract-method
    """
    A custom field to use for the user credential generic relationship.
    """

    def to_representation(self, value):
        """
        Serialize objects to a according to model content-type.
        """
        if isinstance(value, ProgramCertificate):
            return {
                'program_id': value.program_id,
                'credential_id': value.id
            }
        elif isinstance(value, CourseCertificate):
            return {
                'course_id': value.course_id,
                'credential_id': value.id,
                'certificate_type': value.certificate_type
            }


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """ Serializer for CredentialAttribute objects """

    class Meta(object):
        model = UserCredentialAttribute
        fields = ('namespace', 'name', 'value')


class UserCredentialSerializer(serializers.ModelSerializer):
    """ Serializer for User Credential objects. """

    credential = CredentialRelatedField(read_only='True')
    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)

    class Meta(object):
        model = UserCredential
        fields = (
            'id', 'username', 'credential',
            'status', 'download_url', 'uuid', 'attributes', 'created', 'modified'
        )


class ProgramCertificateSerializer(serializers.ModelSerializer):
    """ Serializer for ProgramCertificate objects. """
    user_credential = serializers.SerializerMethodField("get_user_credentials")

    class Meta(object):
        model = ProgramCertificate
        fields = ('user_credential', 'program_id')

    def get_user_credentials(self, program):
        """ Returns all user credentials for a given program."""
        return UserCredentialSerializer(program.user_credentials.all(), many=True).data


class CourseCertificateSerializer(serializers.ModelSerializer):
    """ Serializer for CourseCertificate objects. """

    user_credential = serializers.SerializerMethodField("get_user_credentials")

    class Meta(object):
        model = CourseCertificate
        fields = ('user_credential', 'course_id', 'certificate_type',)

    def get_user_credentials(self, course):
        """ Returns all user credentials for a given program."""
        return UserCredentialSerializer(course.user_credentials.all(), many=True).data
