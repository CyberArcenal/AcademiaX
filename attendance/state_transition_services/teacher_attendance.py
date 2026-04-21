from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.attendance import AttendanceStatus

class TeacherAttendance(TimestampedModel, UUIDModel, SoftDeleteModel):
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    late_minutes = models.PositiveSmallIntegerField(default=0)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_teacher_attendances'
    )

    class Meta:
        unique_together = [['teacher', 'date']]
        ordering = ['-date', 'teacher__last_name']

    def __str__(self):
        return f"{self.teacher} - {self.date} - {self.get_status_display()}"