from rest_framework import serializers
from classes.models.academic_year import AcademicYear
from timetable.models import TimeSlot
from classes.serializers.academic_year import AcademicYearMinimalSerializer


class TimeSlotMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for time slots."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = TimeSlot
        fields = ["id", "name", "day_of_week", "start_time", "end_time", "order", "academic_year"]
        read_only_fields = fields


class TimeSlotCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a time slot."""

    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )

    class Meta:
        model = TimeSlot
        fields = ["name", "day_of_week", "start_time", "end_time", "order", "academic_year_id", "is_active"]

    def create(self, validated_data) -> TimeSlot:
        from timetable.services.time_slot import TimeSlotService

        return TimeSlotService.create_time_slot(**validated_data)


class TimeSlotUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a time slot."""

    class Meta:
        model = TimeSlot
        fields = ["name", "start_time", "end_time", "order", "is_active"]

    def update(self, instance, validated_data) -> TimeSlot:
        from timetable.services.time_slot import TimeSlotService

        return TimeSlotService.update_time_slot(instance, validated_data)


class TimeSlotDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a time slot."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = TimeSlot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]