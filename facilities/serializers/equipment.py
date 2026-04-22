from rest_framework import serializers
from facilities.models import Equipment
from facilities.models.facility import Facility
from .facility import FacilityMinimalSerializer


class EquipmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for equipment."""

    facility = FacilityMinimalSerializer(read_only=True)

    class Meta:
        model = Equipment
        fields = ["id", "name", "facility", "serial_number", "status"]
        read_only_fields = fields


class EquipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating equipment."""

    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="facility", required=False, allow_null=True
    )

    class Meta:
        model = Equipment
        fields = "__all__"

    def create(self, validated_data) -> Equipment:
        from facilities.services.equipment import EquipmentService

        return EquipmentService.create_equipment(**validated_data)


class EquipmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating equipment."""

    class Meta:
        model = Equipment
        fields = ["name", "model", "manufacturer", "status", "notes"]

    def update(self, instance, validated_data) -> Equipment:
        from facilities.services.equipment import EquipmentService

        return EquipmentService.update_equipment(instance, validated_data)


class EquipmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for equipment."""

    facility = FacilityMinimalSerializer(read_only=True)

    class Meta:
        model = Equipment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]