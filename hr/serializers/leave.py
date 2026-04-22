from rest_framework import serializers
from hr.models import LeaveRequest
from hr.models.employee import Employee
from .employee import EmployeeMinimalSerializer


class LeaveRequestMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for leave requests."""

    employee = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ["id", "employee", "leave_type", "start_date", "end_date", "status"]
        read_only_fields = fields


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a leave request."""

    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="employee"
    )

    class Meta:
        model = LeaveRequest
        fields = ["employee_id", "leave_type", "start_date", "end_date", "reason", "remarks"]

    def create(self, validated_data) -> LeaveRequest:
        from hr.services.leave import LeaveRequestService

        return LeaveRequestService.create_leave_request(**validated_data)


class LeaveRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a leave request (approve/reject)."""

    approved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="approved_by", required=False, allow_null=True
    )

    class Meta:
        model = LeaveRequest
        fields = ["status", "approved_by_id", "remarks"]

    def update(self, instance, validated_data) -> LeaveRequest:
        from hr.services.leave import LeaveRequestService

        return LeaveRequestService.update_leave_status(
            instance, validated_data.get('status'),
            validated_data.get('approved_by'), validated_data.get('remarks')
        )


class LeaveRequestDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a leave request."""

    employee = EmployeeMinimalSerializer(read_only=True)
    approved_by = EmployeeMinimalSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "approved_at"]