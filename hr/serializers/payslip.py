from rest_framework import serializers
from hr.models import Payslip
from hr.models.employee import Employee
from hr.models.payroll import PayrollPeriod
from .employee import EmployeeMinimalSerializer
from .payroll import PayrollPeriodMinimalSerializer


class PayslipMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for payslips."""

    employee = EmployeeMinimalSerializer(read_only=True)
    period = PayrollPeriodMinimalSerializer(read_only=True)

    class Meta:
        model = Payslip
        fields = ["id", "employee", "period", "gross_pay", "net_pay", "payment_date"]
        read_only_fields = fields


class PayslipCreateSerializer(serializers.ModelSerializer):
    """Serializer for generating a payslip."""

    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="employee"
    )
    period_id = serializers.PrimaryKeyRelatedField(
        queryset=PayrollPeriod.objects.all(), source="period"
    )

    class Meta:
        model = Payslip
        fields = [
            "employee_id", "period_id", "basic_pay", "overtime_pay", "allowances",
            "bonuses", "sss_contribution", "pagibig_contribution", "philhealth_contribution",
            "withholding_tax", "other_deductions", "bank_account", "notes"
        ]

    def create(self, validated_data) -> Payslip:
        from hr.services.payslip import PayslipService

        return PayslipService.generate_payslip(**validated_data)


class PayslipUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a payslip (payment date, notes)."""

    class Meta:
        model = Payslip
        fields = ["payment_date", "notes", "bank_account"]

    def update(self, instance, validated_data) -> Payslip:
        from hr.services.payslip import PayslipService

        if 'payment_date' in validated_data:
            return PayslipService.mark_paid(instance, validated_data['payment_date'])
        return PayslipService.update_payslip(instance, validated_data)


class PayslipDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a payslip."""

    employee = EmployeeMinimalSerializer(read_only=True)
    period = PayrollPeriodMinimalSerializer(read_only=True)

    class Meta:
        model = Payslip
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]