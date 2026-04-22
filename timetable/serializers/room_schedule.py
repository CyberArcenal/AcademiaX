from rest_framework import serializers
from facilities.models.facility import Facility
from timetable.models import RoomSchedule
from facilities.serializers.facility import FacilityMinimalSerializer
from timetable.models.time_slot import TimeSlot
from .time_slot import TimeSlotMinimalSerializer


class RoomScheduleMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for room schedules."""

    room = FacilityMinimalSerializer(read_only=True)
    time_slot = TimeSlotMinimalSerializer(read_only=True)

    class Meta:
        model = RoomSchedule
        fields = ["id", "room", "time_slot", "event_name", "date"]
        read_only_fields = fields


class RoomScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a room schedule."""

    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="room"
    )
    time_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=TimeSlot.objects.all(), source="time_slot"
    )

    class Meta:
        model = RoomSchedule
        fields = ["room_id", "time_slot_id", "event_name", "description", "date", "is_recurring", "recurring_end_date"]

    def create(self, validated_data) -> RoomSchedule:
        from timetable.services.room_schedule import RoomScheduleService

        return RoomScheduleService.create_room_schedule(**validated_data)


class RoomScheduleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a room schedule."""

    class Meta:
        model = RoomSchedule
        fields = ["event_name", "description", "date", "is_recurring", "recurring_end_date"]

    def update(self, instance, validated_data) -> RoomSchedule:
        from timetable.services.room_schedule import RoomScheduleService

        return RoomScheduleService.update_room_schedule(instance, validated_data)


class RoomScheduleDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a room schedule."""

    room = FacilityMinimalSerializer(read_only=True)
    time_slot = TimeSlotMinimalSerializer(read_only=True)

    class Meta:
        model = RoomSchedule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]