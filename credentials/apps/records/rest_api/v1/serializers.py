from rest_framework import serializers


class ProgramSerializer(serializers.Serializer):  # pylint: disable=abstract-method

    name = serializers.CharField(max_length=255)
    uuid = serializers.UUIDField()
    partner = serializers.CharField(max_length=255)
    completed = serializers.BooleanField()
    empty = serializers.BooleanField()
