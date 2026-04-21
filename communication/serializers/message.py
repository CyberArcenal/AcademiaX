from rest_framework import serializers
from communication.models import Message
from .conversation import ConversationMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class MessageMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for messages."""

    sender = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "content", "created_at", "status"]
        read_only_fields = fields


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a message."""

    conversation_id = serializers.PrimaryKeyRelatedField(
        queryset=Conversation.objects.all(), source="conversation"
    )
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="sender"
    )

    class Meta:
        model = Message
        fields = ["conversation_id", "sender_id", "content"]

    def create(self, validated_data) -> Message:
        from communication.services.message import MessageService

        return MessageService.send_message(**validated_data)


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a message (edit, delete)."""

    class Meta:
        model = Message
        fields = ["content", "is_deleted_for_sender", "is_deleted_for_all"]

    def update(self, instance, validated_data) -> Message:
        from communication.services.message import MessageService

        if 'content' in validated_data:
            return MessageService.edit_message(instance, validated_data['content'])
        if validated_data.get('is_deleted_for_sender'):
            return MessageService.delete_for_sender(instance)
        if validated_data.get('is_deleted_for_all'):
            return MessageService.delete_for_all(instance)
        return instance


class MessageDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a message."""

    conversation = ConversationMinimalSerializer(read_only=True)
    sender = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "delivered_at", "read_at", "edited_at"]