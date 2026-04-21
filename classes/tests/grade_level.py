from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.academic import GradeLevel as GradeLevelChoices

class GradeLevel(TimestampedModel, UUIDModel, SoftDeleteModel):
    level = models.CharField(max_length=10, choices=GradeLevelChoices.choices, unique=True)
    name = models.CharField(max_length=50, help_text="e.g., Grade 7")
    order = models.PositiveSmallIntegerField(unique=True, help_text="1=K, 2=G1, ... 13=G12")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name