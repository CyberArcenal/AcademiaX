from rest_framework import serializers
from academic.models import AcademicProgram


class AcademicProgramMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for academic programs."""

    class Meta:
        model = AcademicProgram
        fields = ["id", "code", "name", "level"]
        read_only_fields = fields


class AcademicProgramCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an academic program."""

    class Meta:
        model = AcademicProgram
        fields = ["code", "name", "level", "description"]

    def create(self, validated_data) -> AcademicProgram:
        from academic.services.academic_program import AcademicProgramService

        return AcademicProgramService.create_program(**validated_data)


class AcademicProgramUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an academic program."""

    class Meta:
        model = AcademicProgram
        fields = ["name", "description", "is_active"]

    def update(self, instance, validated_data) -> AcademicProgram:
        from academic.services.academic_program import AcademicProgramService

        return AcademicProgramService.update_program(instance, validated_data)


class AcademicProgramDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an academic program."""

    class Meta:
        model = AcademicProgram
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]