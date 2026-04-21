from rest_framework import serializers
from communication.models import MessageAttachment
from .message import MessageMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class MessageAttachmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for message attachments."""

    class Meta:
        model = MessageAttachment
        fields = ["id", "file_name", "file_size", "mime_type"]
        read_only_fields = fields


class MessageAttachmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a message attachment."""

    message_id = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(), source="message"
    )
    uploaded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="uploaded_by"
    )

    class Meta:
        model = MessageAttachment
        fields = ["message_id", "file_url", "file_name", "file_size", "mime_type", "uploaded_by_id"]

    def create(self, validated_data) -> MessageAttachment:
        from communication.services.attachment import MessageAttachmentService

        return MessageAttachmentService.create_attachment(**validated_data)


class MessageAttachmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a message attachment (no updates typically)."""

    class Meta:
        model = MessageAttachment
        fields = []  # No updates

    def update(self, instance, validated_data) -> MessageAttachment:
        return instance


class MessageAttachmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a message attachment."""

    message = MessageMinimalSerializer(read_only=True)
    uploaded_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = MessageAttachment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]