from rest_framework import serializers
from hr.models import Position
from .department import DepartmentMinimalSerializer


class PositionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for positions."""

    department = DepartmentMinimalSerializer(read_only=True)

    class Meta:
        model = Position
        fields = ["id", "title", "department", "salary_grade", "is_active"]
        read_only_fields = fields


class PositionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a position."""

    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department"
    )

    class Meta:
        model = Position
        fields = ["title", "department_id", "salary_grade"]

    def create(self, validated_data) -> Position:
        from hr.services.position import PositionService

        return PositionService.create_position(**validated_data)


class PositionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a position."""

    class Meta:
        model = Position
        fields = ["title", "salary_grade", "is_active"]

    def update(self, instance, validated_data) -> Position:
        from hr.services.position import PositionService

        return PositionService.update_position(instance, validated_data)


class PositionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a position."""

    department = DepartmentMinimalSerializer(read_only=True)

    class Meta:
        model = Position
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]