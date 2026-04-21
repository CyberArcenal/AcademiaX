from rest_framework import serializers
from hr.models import SalaryGrade, PayrollPeriod


# SalaryGrade serializers
class SalaryGradeMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for salary grades."""

    class Meta:
        model = SalaryGrade
        fields = ["id", "grade", "basic_salary"]
        read_only_fields = fields


class SalaryGradeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a salary grade."""

    class Meta:
        model = SalaryGrade
        fields = ["grade", "basic_salary", "hourly_rate", "description"]

    def create(self, validated_data) -> SalaryGrade:
        from hr.services.payroll import SalaryGradeService

        return SalaryGradeService.create_salary_grade(**validated_data)


class SalaryGradeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a salary grade."""

    class Meta:
        model = SalaryGrade
        fields = ["basic_salary", "hourly_rate", "description"]

    def update(self, instance, validated_data) -> SalaryGrade:
        from hr.services.payroll import SalaryGradeService

        return SalaryGradeService.update_salary_grade(instance, validated_data)


class SalaryGradeDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a salary grade."""

    class Meta:
        model = SalaryGrade
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


# PayrollPeriod serializers
class PayrollPeriodMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for payroll periods."""

    class Meta:
        model = PayrollPeriod
        fields = ["id", "name", "start_date", "end_date", "is_closed"]
        read_only_fields = fields


class PayrollPeriodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payroll period."""

    class Meta:
        model = PayrollPeriod
        fields = ["name", "start_date", "end_date", "is_closed"]

    def create(self, validated_data) -> PayrollPeriod:
        from hr.services.payroll import PayrollPeriodService

        return PayrollPeriodService.create_payroll_period(**validated_data)


class PayrollPeriodUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a payroll period."""

    class Meta:
        model = PayrollPeriod
        fields = ["name", "is_closed"]

    def update(self, instance, validated_data) -> PayrollPeriod:
        from hr.services.payroll import PayrollPeriodService

        if validated_data.get('is_closed') and not instance.is_closed:
            return PayrollPeriodService.close_period(instance)
        return PayrollPeriodService.update_payroll_period(instance, validated_data)


class PayrollPeriodDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a payroll period."""

    class Meta:
        model = PayrollPeriod
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "closed_at"]