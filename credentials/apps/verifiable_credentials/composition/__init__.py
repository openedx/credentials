"""
Verifiable Credentials different data models specifications.

Composition hierarchy:

CredentialDataModel
|
|_ VerifiableCredentialsDataModel + StatusList2021EntryMixin
|_ OpenBadgesDataModel + StatusList2021EntryMixin
|_ StatusListDataModel
"""

import inspect
from collections import OrderedDict

from rest_framework import serializers

from .schemas import IssuerSchema


class CredentialDataModel(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Basic credential construction machinery.
    """

    VERSION = None
    ID = None
    NAME = None

    context = serializers.SerializerMethodField(
        method_name="collect_context",
        help_text="https://www.w3.org/TR/vc-data-model/#contexts",
    )
    type = serializers.SerializerMethodField(help_text="https://www.w3.org/TR/vc-data-model/#types")
    issuer = IssuerSchema(source="*", help_text="https://www.w3.org/TR/vc-data-model/#issuer")
    issued = serializers.DateTimeField(source="modified", help_text="https://www.w3.org/2018/credentials/#issued")
    issuanceDate = serializers.DateTimeField(
        source="modified",
        help_text="Deprecated (requred by the didkit for now) https://www.w3.org/2018/credentials/#issuanceDate",
    )
    validFrom = serializers.DateTimeField(source="modified", help_text="https://www.w3.org/2018/credentials/#validFrom")
    validUntil = serializers.DateTimeField(
        source="expiration_date",
        help_text="https://www.w3.org/2018/credentials/#validUntil",
    )

    @classmethod
    def get_context(cls):
        """
        Provide root context for all verifiable credentials.
        """
        return [
            "https://www.w3.org/2018/credentials/v1",
            # NOTE: this security context is here intentionally, otherwise wallet verification won't succeed.
            # `DIDKIT` lib also adds it by itself, but not to the "correct/expected" place - into "proof" section.
            "https://w3id.org/security/suites/ed25519-2020/v1",
        ]

    @classmethod
    def get_types(cls):
        """
        Provide root types for all verifiable credentials.
        """
        return [
            "VerifiableCredential",
        ]

    def collect_context(self, __):
        """
        Collect contexts.

        - include default root context
        - include data model context
        """
        return self._collect_hierarchically(class_method="get_context")

    def get_type(self, issuance_line):
        """
        Collect corresponding types.

        - include default root type(s)
        - include data model type(s)
        - include credential-specific type(s)
        """
        data_model_types = self._collect_hierarchically(class_method="get_types")
        credential_types = self.resolve_credential_type(issuance_line)
        return data_model_types + credential_types

    def resolve_credential_type(self, issuance_line):  # pylint: disable=unused-argument
        """
        Map Open edX credential type to data model types.

        Decides: which types should be included based on the source Open edX credential type.
        See:
            https://w3c.github.io/vc-imp-guide/#creating-new-credential-types
            https://schema.org/EducationalOccupationalCredential
        """
        return []

    def _collect_hierarchically(self, class_method):
        """
        Call given method through model MRO and collect returned values.
        """
        values = OrderedDict()
        reversed_mro_classes = reversed(inspect.getmro(type(self)))
        for base_class in reversed_mro_classes:
            if hasattr(base_class, class_method):
                values_list = getattr(base_class, class_method)()
                for value in values_list:
                    values[value] = base_class.__name__
        return list(values.keys())
