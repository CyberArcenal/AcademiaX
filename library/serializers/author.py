from rest_framework import serializers
from library.models import Author


class AuthorMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for authors."""

    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name"]
        read_only_fields = fields


class AuthorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an author."""

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "middle_name", "biography", "birth_date", "death_date"]

    def create(self, validated_data) -> Author:
        from library.services.author import AuthorService

        return AuthorService.create_author(**validated_data)


class AuthorUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an author."""

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "middle_name", "biography", "birth_date", "death_date", "is_active"]

    def update(self, instance, validated_data) -> Author:
        from library.services.author import AuthorService

        return AuthorService.update_author(instance, validated_data)


class AuthorDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an author."""

    class Meta:
        model = Author
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]