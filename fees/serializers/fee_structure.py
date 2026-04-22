from rest_framework import serializers
from academic.models.academic_program import AcademicProgram
from classes.models.academic_year import AcademicYear
from classes.models.grade_level import GradeLevel
from fees.models import FeeStructure
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from classes.serializers.grade_level import GradeLevelMinimalSerializer
from academic.serializers.academic_program import AcademicProgramMinimalSerializer


class FeeStructureMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for fee structures."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = FeeStructure
        fields = ["id", "name", "academic_year", "category", "amount"]
        read_only_fields = fields


class FeeStructureCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a fee structure."""

    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    grade_level_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), source="grade_level", required=False, allow_null=True
    )
    academic_program_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicProgram.objects.all(), source="academic_program", required=False, allow_null=True
    )

    class Meta:
        model = FeeStructure
        fields = "__all__"

    def create(self, validated_data) -> FeeStructure:
        from fees.services.fee_structure import FeeStructureService

        return FeeStructureService.create_fee_structure(**validated_data)


class FeeStructureUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a fee structure."""

    class Meta:
        model = FeeStructure
        fields = ["name", "amount", "is_mandatory", "is_per_semester", "due_date", "description", "is_active"]

    def update(self, instance, validated_data) -> FeeStructure:
        from fees.services.fee_structure import FeeStructureService

        return FeeStructureService.update_fee_structure(instance, validated_data)


class FeeStructureDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a fee structure."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)
    academic_program = AcademicProgramMinimalSerializer(read_only=True)

    class Meta:
        model = FeeStructure
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]