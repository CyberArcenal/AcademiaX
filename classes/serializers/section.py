from rest_framework import serializers
from classes.models import Section
from classes.models.academic_year import AcademicYear
from classes.models.classroom import Classroom
from classes.models.grade_level import GradeLevel
from classes.models.term import Term
from teachers.models.teacher import Teacher
from .grade_level import GradeLevelMinimalSerializer
from .academic_year import AcademicYearMinimalSerializer
from .classroom import ClassroomMinimalSerializer
from .term import TermMinimalSerializer
from teachers.serializers.teacher import TeacherMinimalSerializer


class SectionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for sections."""

    grade_level = GradeLevelMinimalSerializer(read_only=True)

    class Meta:
        model = Section
        fields = ["id", "name", "grade_level", "academic_year", "current_enrollment", "capacity"]
        read_only_fields = fields


class SectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a section."""

    grade_level_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), source="grade_level"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    homeroom_teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="homeroom_teacher", required=False, allow_null=True
    )
    classroom_id = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(), source="classroom", required=False, allow_null=True
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term", required=False, allow_null=True
    )

    class Meta:
        model = Section
        fields = [
            "name", "grade_level_id", "academic_year_id", "homeroom_teacher_id",
            "classroom_id", "term_id", "capacity"
        ]

    def create(self, validated_data) -> Section:
        from classes.services.section import SectionService

        return SectionService.create_section(**validated_data)


class SectionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a section."""

    homeroom_teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="homeroom_teacher", required=False, allow_null=True
    )
    classroom_id = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(), source="classroom", required=False, allow_null=True
    )

    class Meta:
        model = Section
        fields = ["name", "homeroom_teacher_id", "classroom_id", "capacity", "is_active"]

    def update(self, instance, validated_data) -> Section:
        from classes.services.section import SectionService

        return SectionService.update_section(instance, validated_data)


class SectionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a section."""

    grade_level = GradeLevelMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    homeroom_teacher = TeacherMinimalSerializer(read_only=True)
    classroom = ClassroomMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)

    class Meta:
        model = Section
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "current_enrollment"]