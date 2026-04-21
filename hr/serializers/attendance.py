from rest_framework import serializers
from hr.models import EmployeeAttendance
from .employee import EmployeeMinimalSerializer


class EmployeeAttendanceMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for employee attendance."""

    employee = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = EmployeeAttendance
        fields = ["id", "employee", "date", "status", "time_in"]
        read_only_fields = fields


class EmployeeAttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an employee attendance record."""

    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="employee"
    )
    recorded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="recorded_by", required=False, allow_null=True
    )

    class Meta:
        model = EmployeeAttendance
        fields = "__all__"

    def create(self, validated_data) -> EmployeeAttendance:
        from hr.services.attendance import EmployeeAttendanceService

        return EmployeeAttendanceService.create_attendance(**validated_data)


class EmployeeAttendanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an employee attendance record."""

    class Meta:
        model = EmployeeAttendance
        fields = ["status", "time_in", "time_out", "late_minutes", "undertime_minutes", "remarks"]

    def update(self, instance, validated_data) -> EmployeeAttendance:
        from hr.services.attendance import EmployeeAttendanceService

        return EmployeeAttendanceService.update_attendance(instance, validated_data)


class EmployeeAttendanceDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an employee attendance record."""

    employee = EmployeeMinimalSerializer(read_only=True)
    recorded_by = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = EmployeeAttendance
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]