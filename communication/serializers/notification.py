from rest_framework import serializers
from communication.models import Notification
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class NotificationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for notifications."""

    recipient = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "recipient", "title", "is_read", "created_at"]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a notification."""

    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="recipient"
    )

    class Meta:
        model = Notification
        fields = ["recipient_id", "title", "message", "notification_type", "channel", "action_url", "metadata"]

    def create(self, validated_data) -> Notification:
        from communication.services.notification import NotificationService

        return NotificationService.create_notification(**validated_data)


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a notification (mark read)."""

    class Meta:
        model = Notification
        fields = ["is_read"]

    def update(self, instance, validated_data) -> Notification:
        from communication.services.notification import NotificationService

        if validated_data.get('is_read'):
            return NotificationService.mark_as_read(instance)
        return instance


class NotificationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a notification."""

    recipient = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "read_at"]