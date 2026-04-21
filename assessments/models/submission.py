from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel
from common.enums.assessment import SubmissionStatus
from .assessment import Assessment

class Submission(TimestampedModel, UUIDModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='assessment_submissions'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=SubmissionStatus.choices, default=SubmissionStatus.SUBMITTED)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = [['assessment', 'student']]
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} - {self.assessment.title}"