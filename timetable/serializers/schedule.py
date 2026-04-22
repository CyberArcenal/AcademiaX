from rest_framework import serializers
from academic.models.subject import Subject
from classes.models.section import Section
from classes.models.term import Term
from facilities.models.facility import Facility
from teachers.models.teacher import Teacher
from timetable.models import Schedule
from timetable.models.time_slot import TimeSlot
from .time_slot import TimeSlotMinimalSerializer
from classes.serializers.section import SectionMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer
from teachers.serializers.teacher import TeacherMinimalSerializer
from facilities.serializers.facility import FacilityMinimalSerializer
from classes.serializers.term import TermMinimalSerializer


class ScheduleMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for schedules."""

    time_slot = TimeSlotMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    teacher = TeacherMinimalSerializer(read_only=True)
    room = FacilityMinimalSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = ["id", "time_slot", "section", "subject", "teacher", "room", "schedule_type"]
        read_only_fields = fields


class ScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a schedule."""

    time_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=TimeSlot.objects.all(), source="time_slot"
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="room"
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term"
    )

    class Meta:
        model = Schedule
        fields = [
            "time_slot_id", "section_id", "subject_id", "teacher_id", "room_id",
            "term_id", "schedule_type", "notes"
        ]

    def create(self, validated_data) -> Schedule:
        from timetable.services.schedule import ScheduleService

        return ScheduleService.create_schedule(**validated_data)


class ScheduleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a schedule."""

    time_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=TimeSlot.objects.all(), source="time_slot", required=False
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher", required=False
    )
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="room", required=False
    )

    class Meta:
        model = Schedule
        fields = ["time_slot_id", "teacher_id", "room_id", "schedule_type", "notes", "is_active"]

    def update(self, instance, validated_data) -> Schedule:
        from timetable.services.schedule import ScheduleService

        return ScheduleService.update_schedule(instance, validated_data)


class ScheduleDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a schedule."""

    time_slot = TimeSlotMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    teacher = TeacherMinimalSerializer(read_only=True)
    room = FacilityMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]