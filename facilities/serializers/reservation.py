from rest_framework import serializers
from facilities.models import FacilityReservation
from facilities.models.facility import Facility
from users.models.user import User
from .facility import FacilityMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class FacilityReservationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for facility reservations."""

    facility = FacilityMinimalSerializer(read_only=True)
    reserved_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = FacilityReservation
        fields = ["id", "facility", "title", "start_datetime", "end_datetime", "status", "reserved_by"]
        read_only_fields = fields


class FacilityReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a facility reservation."""

    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="facility"
    )
    reserved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="reserved_by"
    )

    class Meta:
        model = FacilityReservation
        fields = ["facility_id", "reserved_by_id", "title", "purpose", "start_datetime", "end_datetime", "attendees_count", "requires_setup", "setup_notes"]

    def create(self, validated_data) -> FacilityReservation:
        from facilities.services.reservation import FacilityReservationService

        return FacilityReservationService.create_reservation(**validated_data)


class FacilityReservationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a facility reservation (approve, reject, cancel)."""

    approved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="approved_by", required=False, allow_null=True
    )

    class Meta:
        model = FacilityReservation
        fields = ["status", "approved_by_id", "cancellation_reason"]

    def update(self, instance, validated_data) -> FacilityReservation:
        from facilities.services.reservation import FacilityReservationService

        if validated_data.get('status') == 'APP':
            return FacilityReservationService.approve_reservation(instance, validated_data.get('approved_by'))
        elif validated_data.get('status') == 'REJ':
            return FacilityReservationService.reject_reservation(instance, validated_data.get('cancellation_reason', ''))
        elif validated_data.get('status') == 'CNC':
            return FacilityReservationService.cancel_reservation(instance, validated_data.get('cancellation_reason', ''))
        return instance


class FacilityReservationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a facility reservation."""

    facility = FacilityMinimalSerializer(read_only=True)
    reserved_by = UserMinimalSerializer(read_only=True)
    approved_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = FacilityReservation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "approved_at"]