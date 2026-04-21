from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from .category import Category

class Product(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    cost = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cost to produce/purchase")
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)
    preparation_time_minutes = models.PositiveSmallIntegerField(default=5)
    is_vegetarian = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)

    class Meta:
        ordering = ['category__display_order', 'name']

    def __str__(self):
        return f"{self.name} - ₱{self.price}"