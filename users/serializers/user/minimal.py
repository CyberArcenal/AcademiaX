from rest_framework import serializers
from users.models import User


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for users."""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "role"]
        read_only_fields = fields