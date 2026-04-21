from django.db import models
from common.base.models import TimestampedModel
from .subject import Subject

class Prerequisite(TimestampedModel):
    """Subject A requires Subject B."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='prerequisites_required')
    required_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='prerequisite_for')
    is_optional = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['subject', 'required_subject']]

    def __str__(self):
        return f"{self.subject.code} requires {self.required_subject.code}"