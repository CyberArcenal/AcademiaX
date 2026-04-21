from rest_framework import serializers
from users.models import User
from .minimal import UserMinimalSerializer


class UserDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a user."""

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ["id", "last_login", "created_at", "updated_at"]