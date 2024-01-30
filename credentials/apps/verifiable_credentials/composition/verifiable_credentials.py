"""
Verifiable Credentials v1.1 data model.

See specification: https://www.w3.org/TR/vc-data-model/
"""

from django.utils.translation import gettext as _
from rest_framework import serializers

from .schemas import CredentialSubjectSchema
from .status_list import CredentialWithStatusList2021DataModel


class VerifiableCredentialsDataModel(CredentialWithStatusList2021DataModel):  # pylint: disable=abstract-method
    """
    Verifiable Credentials data model.
    """

    VERSION = 1.1
    ID = "vc"
    NAME = _("Verifiable Credentials Data Model v1.1")

    id = serializers.UUIDField(
        source="uuid", format="urn", help_text="https://www.w3.org/TR/vc-data-model/#identifiers"
    )
    credentialSubject = CredentialSubjectSchema(
        source="*", help_text="https://www.w3.org/2018/credentials/#credentialSubject"
    )

    class Meta:
        read_only_fields = "__all__"

    def resolve_credential_type(self, issuance_line):
        """
        Map Open edX credential type to data model types.

        Decides: which types should be included based on the source Open edX credential type.
        See:
            https://w3c.github.io/vc-imp-guide/#creating-new-credential-types
            https://schema.org/EducationalOccupationalCredential
        """
        if not issuance_line.user_credential:
            return []

        credential_content_type = issuance_line.user_credential.credential_content_type.model

        # configuration: Open edX internal credential type <> verifiable credential type
        credential_types = {
            "programcertificate": [
                "EducationalOccupationalCredential",
            ],
            "coursecertificate": [
                "EducationalOccupationalCredential",
            ],
        }

        if credential_content_type not in credential_types:
            return []

        return credential_types[credential_content_type]

    @classmethod
    def get_context(cls):
        """
        Provide root context for all verifiable credentials.
        """
        return [
            "https://schema.org/",
        ]
