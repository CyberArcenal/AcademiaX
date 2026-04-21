from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .employee import Employee

class SalaryGrade(TimestampedModel, UUIDModel):
    grade = models.PositiveSmallIntegerField(unique=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Grade {self.grade} - {self.basic_salary}"

class PayrollPeriod(TimestampedModel, UUIDModel):
    name = models.CharField(max_length=100, help_text="e.g., January 1-15, 2025")
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class Payslip(TimestampedModel, UUIDModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payslips')
    basic_pay = models.DecimalField(max_digits=12, decimal_places=2)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    sss_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagibig_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    philhealth_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    withholding_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    bank_account = models.CharField(max_length=50, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    pdf_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['employee', 'period']]
        ordering = ['-period__start_date']

    def __str__(self):
        return f"Payslip for {self.employee} - {self.period.name}"