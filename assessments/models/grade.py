from django.db import models
from common.base.models import TimestampedModel
from .submission import Submission

class AssessmentGrade(TimestampedModel):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='grade_record')
    raw_score = models.DecimalField(max_digits=6, decimal_places=2)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    transmuted_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Grade for {self.submission}"