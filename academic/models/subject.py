from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.academic import SubjectType

class Subject(TimestampedModel, UUIDModel, SoftDeleteModel):
    code = models.CharField(max_length=20, unique=True, help_text="e.g., MATH101")
    name = models.CharField(max_length=200, help_text="e.g., Algebra")
    description = models.TextField(blank=True)
    units = models.DecimalField(max_digits=4, decimal_places=1, default=3.0)
    subject_type = models.CharField(max_length=10, choices=SubjectType.choices, default=SubjectType.CORE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"