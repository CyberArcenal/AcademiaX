from rest_framework import serializers
from users.models import User


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a user."""

    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "middle_name", "suffix",
            "phone_number", "profile_picture", "password"
        ]

    def update(self, instance, validated_data) -> User:
        from users.services.user import UserService

        return UserService.update_user(instance, validated_data)