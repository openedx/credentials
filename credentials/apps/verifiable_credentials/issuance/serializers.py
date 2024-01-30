"""
Verifiable Credentials serializers.
"""

from rest_framework import serializers

from .models import IssuanceLine


class IssuanceLineSerializer(serializers.ModelSerializer):
    """
    Incoming issuance request default serializer.

    It is expected incoming requests from different storages to have unified shape.
    But once it is not the case, swapping this class for something more specific is possible.
    """

    class Meta:
        model = IssuanceLine
        fields = "__all__"
        read_only_fields = ["uuid", "user_credential", "processed", "issuer_id", "storage_id"]

    @staticmethod
    def swap_value(data, source_key, target_key):
        data[target_key] = data.pop(source_key)


class StorageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    id = serializers.CharField(max_length=255, source="ID")
    name = serializers.CharField(max_length=255, source="NAME")

    class Meta:
        read_only_fields = "__all__"
