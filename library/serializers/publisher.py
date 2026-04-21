from rest_framework import serializers
from library.models import Publisher


class PublisherMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for publishers."""

    class Meta:
        model = Publisher
        fields = ["id", "name"]
        read_only_fields = fields


class PublisherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a publisher."""

    class Meta:
        model = Publisher
        fields = ["name", "address", "contact_number", "email", "website"]

    def create(self, validated_data) -> Publisher:
        from library.services.publisher import PublisherService

        return PublisherService.create_publisher(**validated_data)


class PublisherUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a publisher."""

    class Meta:
        model = Publisher
        fields = ["name", "address", "contact_number", "email", "website", "is_active"]

    def update(self, instance, validated_data) -> Publisher:
        from library.services.publisher import PublisherService

        return PublisherService.update_publisher(instance, validated_data)


class PublisherDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a publisher."""

    class Meta:
        model = Publisher
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]