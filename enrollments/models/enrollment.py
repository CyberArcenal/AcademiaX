from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.enrollment import EnrollmentStatus, DropReason, EnrollmentPaymentStatus

class Enrollment(TimestampedModel, UUIDModel, SoftDeleteModel):
    # Core relationships
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    academic_year = models.ForeignKey(
        'classes.AcademicYear',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    grade_level = models.ForeignKey(
        'classes.GradeLevel',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    section = models.ForeignKey(
        'classes.Section',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    status = models.CharField(
        max_length=10,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING
    )
    enrollment_date = models.DateField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=10,
        choices=EnrollmentPaymentStatus.choices,
        default=EnrollmentPaymentStatus.UNPAID
    )
    # Optional tracking
    previous_school = models.CharField(max_length=200, blank=True, help_text="If transferee")
    lrn = models.CharField(max_length=20, blank=True, help_text="Learner Reference Number")
    drop_reason = models.CharField(max_length=10, choices=DropReason.choices, blank=True, null=True)
    drop_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_enrollments'
    )

    class Meta:
        unique_together = [['student', 'academic_year']]  # One enrollment per student per school year
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['status', 'academic_year']),
            models.Index(fields=['student', 'status']),
        ]

    def __str__(self):
        return f"{self.student} - {self.academic_year.name} - {self.get_status_display()}"