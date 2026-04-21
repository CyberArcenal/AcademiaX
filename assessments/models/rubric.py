from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .assessment import Assessment

class RubricCriterion(TimestampedModel, UUIDModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='rubric_criteria')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_points = models.DecimalField(max_digits=6, decimal_places=2)
    order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.assessment.title} - {self.name}"

class RubricLevel(TimestampedModel):
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE, related_name='levels')
    level_name = models.CharField(max_length=100)  # e.g., Excellent, Good, Fair, Poor
    description = models.TextField(blank=True)
    points = models.DecimalField(max_digits=6, decimal_places=2)
    
    class Meta:
        ordering = ['-points']

    def __str__(self):
        return f"{self.criterion.name} - {self.level_name}: {self.points}"