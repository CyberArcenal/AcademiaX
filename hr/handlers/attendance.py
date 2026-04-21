from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.hr import AttendanceStatus
from .employee import Employee

class EmployeeAttendance(TimestampedModel, UUIDModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    late_minutes = models.PositiveIntegerField(default=0)
    undertime_minutes = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_attendances')

    class Meta:
        unique_together = [['employee', 'date']]
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.get_status_display()}"