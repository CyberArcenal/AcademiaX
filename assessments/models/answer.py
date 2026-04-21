from django.db import models
from common.base.models import TimestampedModel
from .submission import Submission
from .question import Question
from .choice import Choice

class Answer(TimestampedModel):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # Para sa multiple choice / true-false
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    # Para sa essay/identification
    text_answer = models.TextField(blank=True)
    # Para sa matching type (store as JSON)
    matching_answer = models.JSONField(null=True, blank=True)
    # Score for this specific answer
    points_earned = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = [['submission', 'question']]

    def __str__(self):
        return f"Answer for {self.submission} - Q{self.question.id}"