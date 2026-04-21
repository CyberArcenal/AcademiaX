from rest_framework import serializers
from hr.models import Department
from .employee import EmployeeMinimalSerializer


class DepartmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for departments."""

    head = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "code", "head", "is_active"]
        read_only_fields = fields


class DepartmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a department."""

    head_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="head", required=False, allow_null=True
    )

    class Meta:
        model = Department
        fields = ["name", "code", "description", "head_id"]

    def create(self, validated_data) -> Department:
        from hr.services.department import DepartmentService

        return DepartmentService.create_department(**validated_data)


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a department."""

    head_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="head", required=False, allow_null=True
    )

    class Meta:
        model = Department
        fields = ["name", "code", "description", "head_id", "is_active"]

    def update(self, instance, validated_data) -> Department:
        from hr.services.department import DepartmentService

        return DepartmentService.update_department(instance, validated_data)


class DepartmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a department."""

    head = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]