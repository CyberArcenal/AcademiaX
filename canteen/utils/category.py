from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.canteen import ProductCategory

class Category(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=50, choices=ProductCategory.choices, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.get_name_display()