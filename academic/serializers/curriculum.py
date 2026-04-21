from rest_framework import serializers
from academic.models import Curriculum
from academic.models.academic_program import AcademicProgram
from .academic_program import AcademicProgramMinimalSerializer


class CurriculumMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for curricula."""

    academic_program = AcademicProgramMinimalSerializer(read_only=True)

    class Meta:
        model = Curriculum
        fields = ["id", "academic_program", "grade_level", "year_effective", "is_current"]
        read_only_fields = fields


class CurriculumCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a curriculum."""

    academic_program_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicProgram.objects.all(), source="academic_program"
    )

    class Meta:
        model = Curriculum
        fields = ["academic_program_id", "grade_level", "year_effective", "is_current"]

    def create(self, validated_data) -> Curriculum:
        from academic.services.curriculum import CurriculumService

        return CurriculumService.create_curriculum(**validated_data)


class CurriculumUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a curriculum."""

    class Meta:
        model = Curriculum
        fields = ["year_effective", "is_current"]

    def update(self, instance, validated_data) -> Curriculum:
        from academic.services.curriculum import CurriculumService

        return CurriculumService.update_curriculum(instance, validated_data)


class CurriculumDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a curriculum."""

    academic_program = AcademicProgramMinimalSerializer(read_only=True)

    class Meta:
        model = Curriculum
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]