from rest_framework import serializers
from hr.models import Employee
from hr.models.department import Department
from hr.models.position import Position

from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class EmployeeMinimalSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "employee_number", "user", "position", "status"]
        read_only_fields = fields


class EmployeeCreateSerializer(serializers.ModelSerializer):
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
    user = UserMinimalSerializer(read_only=True)
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    supervisor = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "employee_number"]

    def get_department(self, obj):
        if obj.department:
            from hr.serializers.department import DepartmentMinimalSerializer
            return DepartmentMinimalSerializer(obj.department).data
        return None

    def get_position(self, obj):
        if obj.position:
            from hr.serializers.position import PositionMinimalSerializer
            return PositionMinimalSerializer(obj.position).data
        return None

    def get_supervisor(self, obj):
        if obj.supervisor:
            from hr.serializers.employee import EmployeeMinimalSerializer
            return EmployeeMinimalSerializer(obj.supervisor).data
        return None