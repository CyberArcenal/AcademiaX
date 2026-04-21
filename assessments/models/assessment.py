from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.assessment import AssessmentType

class Assessment(TimestampedModel, UUIDModel, SoftDeleteModel):
    # Relasyon sa subject (from academic app)
    subject = models.ForeignKey(
        'academic.Subject',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    # Teacher na gumawa (from teachers app)
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assessment_type = models.CharField(max_length=10, choices=AssessmentType.choices)
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    passing_points = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    due_date = models.DateTimeField(null=True, blank=True)
    open_date = models.DateTimeField(null=True, blank=True)
    close_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    allow_late_submission = models.BooleanField(default=False)
    late_deduction_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attempts_allowed = models.PositiveSmallIntegerField(default=1)
    show_answers_after_submission = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', 'is_published']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.subject.code} - {self.title}"