from rest_framework import serializers
from grades.models import GradeComponent
from academic.serializers.subject import SubjectMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from classes.serializers.grade_level import GradeLevelMinimalSerializer


class GradeComponentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for grade components."""

    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = GradeComponent
        fields = ["id", "subject", "name", "weight", "is_active"]
        read_only_fields = fields


class GradeComponentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a grade component."""

    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    grade_level_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), source="grade_level"
    )

    class Meta:
        model = GradeComponent
        fields = ["name", "weight", "subject_id", "academic_year_id", "grade_level_id", "is_active"]

    def create(self, validated_data) -> GradeComponent:
        from grades.services.grade_component import GradeComponentService

        return GradeComponentService.create_component(**validated_data)


class GradeComponentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a grade component."""

    class Meta:
        model = GradeComponent
        fields = ["name", "weight", "is_active"]

    def update(self, instance, validated_data) -> GradeComponent:
        from grades.services.grade_component import GradeComponentService

        return GradeComponentService.update_component(instance, validated_data)


class GradeComponentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a grade component."""

    subject = SubjectMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)

    class Meta:
        model = GradeComponent
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]