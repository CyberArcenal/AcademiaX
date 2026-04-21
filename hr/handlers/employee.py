from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.hr import EmploymentType, EmploymentStatus
from .department import Department
from .position import Position

class Employee(TimestampedModel, UUIDModel, SoftDeleteModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_record'
    )
    employee_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, related_name='employees')
    employment_type = models.CharField(max_length=10, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    status = models.CharField(max_length=10, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE)
    hire_date = models.DateField()
    regularized_date = models.DateField(null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    contact_number = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True)
    tin = models.CharField(max_length=20, blank=True, help_text="Tax Identification Number")
    sss = models.CharField(max_length=20, blank=True)
    pagibig = models.CharField(max_length=20, blank=True)
    philhealth = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['employee_number']

    def __str__(self):
        return f"{self.employee_number} - {self.user.get_full_name()}"