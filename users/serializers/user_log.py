from rest_framework import serializers
from users.models.user import User
from users.models.user_log import UserLog
from .user.minimal import UserMinimalSerializer


class UserLogMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for user logs."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = UserLog
        fields = ["id", "user", "action", "created_at"]
        read_only_fields = fields


class UserLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a user log (usually internal)."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user"
    )

    class Meta:
        model = UserLog
        fields = ["user_id", "action", "ip_address", "user_agent", "details"]

    def create(self, validated_data) -> UserLog:
        from users.services.user_log import UserLogService

        return UserLogService.create_log(**validated_data)


class UserLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a user log (not typically allowed)."""

    class Meta:
        model = UserLog
        fields = []  # No updates

    def update(self, instance, validated_data) -> UserLog:
        return instance


class UserLogDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a user log."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = UserLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]