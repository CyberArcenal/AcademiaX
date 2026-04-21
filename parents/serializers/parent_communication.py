from rest_framework import serializers
from parents.models import ParentCommunicationLog
from parents.models.parent import Parent
from users.models.user import User
from .parent import ParentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class ParentCommunicationLogMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for parent communication logs."""

    parent = ParentMinimalSerializer(read_only=True)

    class Meta:
        model = ParentCommunicationLog
        fields = ["id", "parent", "subject", "channel", "direction", "created_at"]
        read_only_fields = fields


class ParentCommunicationLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a parent communication log."""

    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(), source="parent"
    )
    sent_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="sent_by", required=False, allow_null=True
    )

    class Meta:
        model = ParentCommunicationLog
        fields = ["parent_id", "subject", "message", "channel", "direction", "sent_by_id", "follow_up_required"]

    def create(self, validated_data) -> ParentCommunicationLog:
        from parents.services.parent_communication import ParentCommunicationLogService

        return ParentCommunicationLogService.create_log(**validated_data)


class ParentCommunicationLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a parent communication log (resolve)."""

    resolved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="resolved_by", required=False, allow_null=True
    )

    class Meta:
        model = ParentCommunicationLog
        fields = ["is_resolved", "resolved_by_id"]

    def update(self, instance, validated_data) -> ParentCommunicationLog:
        from parents.services.parent_communication import ParentCommunicationLogService

        if validated_data.get('is_resolved') and not instance.is_resolved:
            return ParentCommunicationLogService.resolve_log(instance, validated_data.get('resolved_by'))
        return ParentCommunicationLogService.update_log(instance, validated_data)


class ParentCommunicationLogDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a parent communication log."""

    parent = ParentMinimalSerializer(read_only=True)
    sent_by = UserMinimalSerializer(read_only=True)
    resolved_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ParentCommunicationLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "resolved_at"]