from rest_framework import serializers
from timetable.models import ScheduleOverride
from .schedule import ScheduleMinimalSerializer
from facilities.serializers.facility import FacilityMinimalSerializer
from teachers.serializers.teacher import TeacherMinimalSerializer


class ScheduleOverrideMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for schedule overrides."""

    schedule = ScheduleMinimalSerializer(read_only=True)

    class Meta:
        model = ScheduleOverride
        fields = ["id", "schedule", "date", "is_cancelled"]
        read_only_fields = fields


class ScheduleOverrideCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a schedule override."""

    schedule_id = serializers.PrimaryKeyRelatedField(
        queryset=Schedule.objects.all(), source="schedule"
    )
    new_room_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="new_room", required=False, allow_null=True
    )
    new_teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="new_teacher", required=False, allow_null=True
    )

    class Meta:
        model = ScheduleOverride
        fields = [
            "schedule_id", "date", "new_start_time", "new_end_time",
            "new_room_id", "new_teacher_id", "reason", "is_cancelled"
        ]

    def create(self, validated_data) -> ScheduleOverride:
        from timetable.services.schedule_override import ScheduleOverrideService

        return ScheduleOverrideService.create_override(**validated_data)


class ScheduleOverrideUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a schedule override."""

    new_room_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="new_room", required=False, allow_null=True
    )
    new_teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="new_teacher", required=False, allow_null=True
    )

    class Meta:
        model = ScheduleOverride
        fields = ["new_start_time", "new_end_time", "new_room_id", "new_teacher_id", "reason", "is_cancelled"]

    def update(self, instance, validated_data) -> ScheduleOverride:
        from timetable.services.schedule_override import ScheduleOverrideService

        return ScheduleOverrideService.update_override(instance, validated_data)


class ScheduleOverrideDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a schedule override."""

    schedule = ScheduleMinimalSerializer(read_only=True)
    new_room = FacilityMinimalSerializer(read_only=True)
    new_teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = ScheduleOverride
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]