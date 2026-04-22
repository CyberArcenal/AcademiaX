from rest_framework import serializers
from parents.models import Parent
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class ParentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for parents."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Parent
        fields = ["id", "user", "contact_number", "status"]
        read_only_fields = fields


class ParentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a parent record."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user"
    )

    class Meta:
        model = Parent
        fields = [
            "user_id", "contact_number", "alternative_contact", "email",
            "occupation", "employer", "employer_address", "emergency_contact_name",
            "emergency_contact_number", "preferred_language", "receive_notifications",
            "receive_email_digest"
        ]

    def create(self, validated_data) -> Parent:
        from parents.services.parent import ParentService

        return ParentService.create_parent(**validated_data)


class ParentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a parent record."""

    class Meta:
        model = Parent
        fields = [
            "contact_number", "alternative_contact", "email", "occupation",
            "employer", "employer_address", "emergency_contact_name",
            "emergency_contact_number", "preferred_language",
            "receive_notifications", "receive_email_digest", "status"
        ]

    def update(self, instance, validated_data) -> Parent:
        from parents.services.parent import ParentService

        return ParentService.update_parent(instance, validated_data)


class ParentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a parent."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Parent
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]