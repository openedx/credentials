"""
Complementary schemas for verifiable credential composition.
"""

from rest_framework import serializers


class EducationalOccupationalProgramSchema(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Defines Open edX Program.
    """

    TYPE = "EducationalOccupationalProgram"

    id = serializers.CharField(default=TYPE, help_text="https://schema.org/EducationalOccupationalProgram")
    name = serializers.CharField(source="user_credential.credential.program.title")
    description = serializers.CharField(source="user_credential.credential.program_uuid")

    class Meta:
        read_only_fields = "__all__"


class EducationalOccupationalCredentialSchema(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Defines Open edX user credential.
    """

    TYPE = "EducationalOccupationalCredential"

    id = serializers.CharField(default=TYPE, help_text="https://schema.org/EducationalOccupationalCredential")
    name = serializers.CharField(source="user_credential.credential.title")
    description = serializers.CharField(source="user_credential.uuid")
    program = EducationalOccupationalProgramSchema(source="*")

    class Meta:
        read_only_fields = "__all__"


class CredentialSubjectSchema(serializers.Serializer):  # pylint: disable=abstract-method
    id = serializers.CharField(source="subject_id")
    hasCredential = EducationalOccupationalCredentialSchema(source="*")

    class Meta:
        read_only_fields = "__all__"


class IssuerSchema(serializers.Serializer):  # pylint: disable=abstract-method
    TYPE = "Profile"

    id = serializers.CharField(source="issuer_id")
    type = serializers.CharField(default=TYPE)
    name = serializers.CharField(source="issuer_name")

    class Meta:
        read_only_fields = "__all__"
