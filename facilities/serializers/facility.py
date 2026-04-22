from rest_framework import serializers
from facilities.models import Facility
from facilities.models.building import Building
from .building import BuildingMinimalSerializer


class FacilityMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for facilities."""

    building = BuildingMinimalSerializer(read_only=True)

    class Meta:
        model = Facility
        fields = ["id", "name", "building", "facility_type", "status", "capacity"]
        read_only_fields = fields


class FacilityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a facility."""

    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(), source="building"
    )

    class Meta:
        model = Facility
        fields = "__all__"

    def create(self, validated_data) -> Facility:
        from facilities.services.facility import FacilityService

        return FacilityService.create_facility(**validated_data)


class FacilityUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a facility."""

    class Meta:
        model = Facility
        fields = ["name", "facility_type", "room_number", "floor", "capacity", "status", "description", "features", "is_active"]

    def update(self, instance, validated_data) -> Facility:
        from facilities.services.facility import FacilityService

        return FacilityService.update_facility(instance, validated_data)


class FacilityDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a facility."""

    building = BuildingMinimalSerializer(read_only=True)

    class Meta:
        model = Facility
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]