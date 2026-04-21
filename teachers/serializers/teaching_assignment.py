from rest_framework import serializers
from teachers.models import TeachingAssignment
from .teacher import TeacherMinimalSerializer
from classes.serializers.section import SectionMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from classes.serializers.term import TermMinimalSerializer


class TeachingAssignmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for teaching assignments."""

    teacher = TeacherMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = TeachingAssignment
        fields = ["id", "teacher", "section", "subject", "academic_year", "is_active"]
        read_only_fields = fields


class TeachingAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a teaching assignment."""

    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term", required=False, allow_null=True
    )

    class Meta:
        model = TeachingAssignment
        fields = ["teacher_id", "section_id", "subject_id", "academic_year_id", "term_id", "is_active"]

    def create(self, validated_data) -> TeachingAssignment:
        from teachers.services.teaching_assignment import TeachingAssignmentService

        return TeachingAssignmentService.create_assignment(**validated_data)


class TeachingAssignmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a teaching assignment."""

    class Meta:
        model = TeachingAssignment
        fields = ["is_active"]

    def update(self, instance, validated_data) -> TeachingAssignment:
        from teachers.services.teaching_assignment import TeachingAssignmentService

        return TeachingAssignmentService.update_assignment(instance, validated_data)


class TeachingAssignmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a teaching assignment."""

    teacher = TeacherMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)

    class Meta:
        model = TeachingAssignment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]