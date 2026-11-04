"""Serializers for the assistant app."""

from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """Validates an incoming chat message."""

    message = serializers.CharField(trim_whitespace=True, max_length=2000)

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError('Message cannot be empty.')
        return value
