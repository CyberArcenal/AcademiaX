from django.db import models
from common.base.models import TimestampedModel, UUIDModel

class Holiday(TimestampedModel, UUIDModel):
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    is_school_wide = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} - {self.date}"