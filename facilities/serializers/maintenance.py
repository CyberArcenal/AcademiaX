from rest_framework import serializers
from facilities.models import MaintenanceRequest
from .facility import FacilityMinimalSerializer
from .equipment import EquipmentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class MaintenanceRequestMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for maintenance requests."""

    facility = FacilityMinimalSerializer(read_only=True)
    equipment = EquipmentMinimalSerializer(read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = ["id", "title", "facility", "equipment", "priority", "status", "created_at"]
        read_only_fields = fields


class MaintenanceRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a maintenance request."""

    reported_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="reported_by"
    )
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="facility", required=False, allow_null=True
    )
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(), source="equipment", required=False, allow_null=True
    )
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="assigned_to", required=False, allow_null=True
    )

    class Meta:
        model = MaintenanceRequest
        fields = "__all__"

    def create(self, validated_data) -> MaintenanceRequest:
        from facilities.services.maintenance import MaintenanceRequestService

        return MaintenanceRequestService.create_request(**validated_data)


class MaintenanceRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a maintenance request."""

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="assigned_to", required=False, allow_null=True
    )

    class Meta:
        model = MaintenanceRequest
        fields = ["priority", "status", "assigned_to_id", "scheduled_date", "completed_date", "cost", "remarks"]

    def update(self, instance, validated_data) -> MaintenanceRequest:
        from facilities.services.maintenance import MaintenanceRequestService

        return MaintenanceRequestService.update_request(instance, validated_data)


class MaintenanceRequestDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a maintenance request."""

    facility = FacilityMinimalSerializer(read_only=True)
    equipment = EquipmentMinimalSerializer(read_only=True)
    reported_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]