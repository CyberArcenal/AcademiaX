from rest_framework import serializers
from communication.models import BroadcastLog
from .announcement import AnnouncementMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class BroadcastLogMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for broadcast logs."""

    announcement = AnnouncementMinimalSerializer(read_only=True)
    recipient = UserMinimalSerializer(read_only=True)

    class Meta:
        model = BroadcastLog
        fields = ["id", "announcement", "recipient", "channel", "status", "sent_at"]
        read_only_fields = fields


class BroadcastLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a broadcast log."""

    announcement_id = serializers.PrimaryKeyRelatedField(
        queryset=Announcement.objects.all(), source="announcement"
    )
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="recipient"
    )

    class Meta:
        model = BroadcastLog
        fields = ["announcement_id", "recipient_id", "channel", "status", "error_message"]

    def create(self, validated_data) -> BroadcastLog:
        from communication.services.broadcast_log import BroadcastLogService

        return BroadcastLogService.create_log(**validated_data)


class BroadcastLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a broadcast log (status)."""

    class Meta:
        model = BroadcastLog
        fields = ["status", "error_message"]

    def update(self, instance, validated_data) -> BroadcastLog:
        from communication.services.broadcast_log import BroadcastLogService

        return BroadcastLogService.update_status(instance, validated_data.get('status'), validated_data.get('error_message', ''))


class BroadcastLogDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a broadcast log."""

    announcement = AnnouncementMinimalSerializer(read_only=True)
    recipient = UserMinimalSerializer(read_only=True)

    class Meta:
        model = BroadcastLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]