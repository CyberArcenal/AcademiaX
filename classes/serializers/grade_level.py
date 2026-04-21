from rest_framework import serializers
from classes.models import GradeLevel


class GradeLevelMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for grade levels."""

    class Meta:
        model = GradeLevel
        fields = ["id", "level", "name", "order"]
        read_only_fields = fields


class GradeLevelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a grade level."""

    class Meta:
        model = GradeLevel
        fields = ["level", "name", "order"]

    def create(self, validated_data) -> GradeLevel:
        from classes.services.grade_level import GradeLevelService

        return GradeLevelService.create_grade_level(**validated_data)


class GradeLevelUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a grade level."""

    class Meta:
        model = GradeLevel
        fields = ["name", "order"]

    def update(self, instance, validated_data) -> GradeLevel:
        from classes.services.grade_level import GradeLevelService

        return GradeLevelService.update_grade_level(instance, validated_data)


class GradeLevelDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a grade level."""

    class Meta:
        model = GradeLevel
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]