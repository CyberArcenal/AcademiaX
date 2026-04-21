from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel

class AcademicYear(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=20, unique=True, help_text="e.g., 2025-2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name