from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.attendance import AttendanceStatus, LateReason

class StudentAttendance(TimestampedModel, UUIDModel, SoftDeleteModel):
    # Relasyon
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    section = models.ForeignKey(
        'classes.Section',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    subject = models.ForeignKey(
        'academic.Subject',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    academic_year = models.ForeignKey(
        'classes.AcademicYear',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    late_minutes = models.PositiveSmallIntegerField(default=0)
    late_reason = models.CharField(max_length=10, choices=LateReason.choices, null=True, blank=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances'
    )

    class Meta:
        unique_together = [['student', 'subject', 'date', 'section']]
        ordering = ['-date', 'student__last_name']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['section', 'date']),
        ]

    def __str__(self):
        return f"{self.student} - {self.subject.code} - {self.date} - {self.get_status_display()}"