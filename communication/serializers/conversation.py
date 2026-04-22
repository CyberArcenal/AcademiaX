from rest_framework import serializers
from communication.models import Conversation
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class ConversationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for conversations."""

    participants = UserMinimalSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "name", "conversation_type", "participants", "last_message", "last_message_at"]
        read_only_fields = fields


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a conversation."""

    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="participants", many=True
    )
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by"
    )

    class Meta:
        model = Conversation
        fields = ["conversation_type", "name", "participant_ids", "created_by_id"]

    def create(self, validated_data) -> Conversation:
        from communication.services.conversation import ConversationService

        participants = validated_data.pop('participants')
        created_by = validated_data.pop('created_by')
        return ConversationService.create_conversation(participants, created_by, **validated_data)


class ConversationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a conversation (name, add/remove participants)."""

    add_participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )
    remove_participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Conversation
        fields = ["name", "add_participant_ids", "remove_participant_ids"]

    def update(self, instance, validated_data) -> Conversation:
        from communication.services.conversation import ConversationService

        if 'name' in validated_data:
            instance.name = validated_data['name']
            instance.save()
        for user in validated_data.get('add_participant_ids', []):
            ConversationService.add_participant(instance, user)
        for user in validated_data.get('remove_participant_ids', []):
            ConversationService.remove_participant(instance, user)
        return instance


class ConversationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a conversation."""

    participants = UserMinimalSerializer(many=True, read_only=True)
    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "last_message_at"]