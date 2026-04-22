from rest_framework import serializers
from facilities.models import FacilityUsageLog
from facilities.models.facility import Facility
from facilities.models.reservation import FacilityReservation
from users.models.user import User
from .facility import FacilityMinimalSerializer
from .reservation import FacilityReservationMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class FacilityUsageLogMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for facility usage logs."""

    facility = FacilityMinimalSerializer(read_only=True)
    used_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = FacilityUsageLog
        fields = ["id", "facility", "used_by", "check_in", "check_out"]
        read_only_fields = fields


class FacilityUsageLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a facility usage log."""

    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="facility"
    )
    used_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="used_by"
    )
    reservation_id = serializers.PrimaryKeyRelatedField(
        queryset=FacilityReservation.objects.all(), source="reservation", required=False, allow_null=True
    )

    class Meta:
        model = FacilityUsageLog
        fields = ["facility_id", "used_by_id", "reservation_id", "check_in", "condition_before", "notes"]

    def create(self, validated_data) -> FacilityUsageLog:
        from facilities.services.usage_log import FacilityUsageLogService

        return FacilityUsageLogService.create_usage_log(**validated_data)


class FacilityUsageLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a facility usage log (check out)."""

    class Meta:
        model = FacilityUsageLog
        fields = ["check_out", "condition_after", "notes"]

    def update(self, instance, validated_data) -> FacilityUsageLog:
        from facilities.services.usage_log import FacilityUsageLogService

        return FacilityUsageLogService.check_out(instance, validated_data.get('condition_after', ''), validated_data.get('notes', ''))


class FacilityUsageLogDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a facility usage log."""

    facility = FacilityMinimalSerializer(read_only=True)
    reservation = FacilityReservationMinimalSerializer(read_only=True)
    used_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = FacilityUsageLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]