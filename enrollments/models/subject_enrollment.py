from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .enrollment import Enrollment

class SubjectEnrollment(TimestampedModel, UUIDModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='subject_enrollments')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    is_dropped = models.BooleanField(default=False)
    drop_date = models.DateField(null=True, blank=True)
    drop_reason = models.CharField(max_length=10, blank=True)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [['enrollment', 'subject']]
        ordering = ['enrollment', 'subject__code']

    def __str__(self):
        return f"{self.enrollment.student} - {self.subject.code}"