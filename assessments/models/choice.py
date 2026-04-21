from django.db import models
from common.base.models import TimestampedModel
from .question import Question

class Choice(TimestampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = [['question', 'order']]

    def __str__(self):
        return f"{self.question.id} - {self.choice_text[:30]}"