from rest_framework import serializers
from facilities.models import Building


class BuildingMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for buildings."""

    class Meta:
        model = Building
        fields = ["id", "name", "code", "is_active"]
        read_only_fields = fields


class BuildingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a building."""

    class Meta:
        model = Building
        fields = ["name", "code", "address", "number_of_floors", "year_built"]

    def create(self, validated_data) -> Building:
        from facilities.services.building import BuildingService

        return BuildingService.create_building(**validated_data)


class BuildingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a building."""

    class Meta:
        model = Building
        fields = ["name", "code", "address", "number_of_floors", "year_built", "is_active"]

    def update(self, instance, validated_data) -> Building:
        from facilities.services.building import BuildingService

        return BuildingService.update_building(instance, validated_data)


class BuildingDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a building."""

    class Meta:
        model = Building
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]