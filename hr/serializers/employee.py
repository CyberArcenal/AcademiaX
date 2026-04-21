from rest_framework import serializers
from hr.models import Employee
from users.serializers.user.minimal import UserMinimalSerializer
from .department import DepartmentMinimalSerializer
from .position import PositionMinimalSerializer


class EmployeeMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for employees."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "employee_number", "user", "position", "status"]
        read_only_fields = fields


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an employee."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user"
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department", required=False, allow_null=True
    )
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), source="position", required=False, allow_null=True
    )
    supervisor_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="supervisor", required=False, allow_null=True
    )

    class Meta:
        model = Employee
        fields = [
            "user_id", "employee_number", "department_id", "position_id",
            "employment_type", "hire_date", "regularized_date", "supervisor_id",
            "contact_number", "emergency_contact_name", "emergency_contact_number",
            "tin", "sss", "pagibig", "philhealth"
        ]

    def create(self, validated_data) -> Employee:
        from hr.services.employee import EmployeeService

        return EmployeeService.create_employee(**validated_data)


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an employee."""

    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department", required=False, allow_null=True
    )
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), source="position", required=False, allow_null=True
    )
    supervisor_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="supervisor", required=False, allow_null=True
    )

    class Meta:
        model = Employee
        fields = [
            "department_id", "position_id", "employment_type", "status",
            "regularized_date", "supervisor_id", "contact_number",
            "emergency_contact_name", "emergency_contact_number",
            "tin", "sss", "pagibig", "philhealth"
        ]

    def update(self, instance, validated_data) -> Employee:
        from hr.services.employee import EmployeeService

        return EmployeeService.update_employee(instance, validated_data)


class EmployeeDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an employee."""

    user = UserMinimalSerializer(read_only=True)
    department = DepartmentMinimalSerializer(read_only=True)
    position = PositionMinimalSerializer(read_only=True)
    supervisor = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "employee_number"]