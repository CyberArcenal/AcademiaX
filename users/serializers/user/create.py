from rest_framework import serializers
from users.models import User


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a user."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username", "email", "password", "first_name", "last_name",
            "middle_name", "suffix", "phone_number", "role"
        ]

    def create(self, validated_data) -> User:
        from users.services.user import UserService

        return UserService.create_user(**validated_data)