from rest_framework import serializers
from library.models import Reservation
from .copy import BookCopyMinimalSerializer
from students.serializers.student import StudentMinimalSerializer


class ReservationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for reservations."""

    copy = BookCopyMinimalSerializer(read_only=True)
    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = ["id", "copy", "student", "reservation_date", "expiry_date", "is_active"]
        read_only_fields = fields


class ReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a reservation."""

    copy_id = serializers.PrimaryKeyRelatedField(
        queryset=BookCopy.objects.all(), source="copy"
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )

    class Meta:
        model = Reservation
        fields = ["copy_id", "student_id", "expiry_date"]

    def create(self, validated_data) -> Reservation:
        from library.services.reservation import ReservationService

        return ReservationService.create_reservation(**validated_data)


class ReservationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a reservation (cancel, fulfill)."""

    class Meta:
        model = Reservation
        fields = ["is_active"]

    def update(self, instance, validated_data) -> Reservation:
        from library.services.reservation import ReservationService

        if not validated_data.get('is_active', True):
            return ReservationService.cancel_reservation(instance)
        return instance


class ReservationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a reservation."""

    copy = BookCopyMinimalSerializer(read_only=True)
    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "fulfilled_at", "cancelled_at"]