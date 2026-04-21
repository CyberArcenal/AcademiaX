from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .subject import Subject

class LearningOutcome(TimestampedModel, UUIDModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='learning_outcomes')
    code = models.CharField(max_length=20)  # e.g., LO1, LO2
    description = models.TextField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [['subject', 'code']]
        ordering = ['subject', 'order']

    def __str__(self):
        return f"{self.subject.code} - {self.code}: {self.description[:50]}"