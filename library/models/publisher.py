from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel

class Publisher(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name