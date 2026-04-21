from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.assessment import QuestionType
from .assessment import Assessment

class Question(TimestampedModel, UUIDModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QuestionType.choices)
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    order = models.PositiveSmallIntegerField(default=0, help_text="Sequence in the assessment")
    explanation = models.TextField(blank=True, help_text="Explanation for correct answer")
    is_required = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['assessment', 'order']),
        ]

    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}: {self.question_text[:50]}"