from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel

class Building(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    number_of_floors = models.PositiveSmallIntegerField(default=1)
    year_built = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name