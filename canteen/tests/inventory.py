from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .product import Product

class InventoryLog(TimestampedModel, UUIDModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    quantity_change = models.IntegerField(help_text="Positive for stock-in, negative for stock-out")
    new_quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=100, choices=[
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('WASTE', 'Waste'),
        ('ADJUSTMENT', 'Adjustment'),
    ])
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name}: {self.quantity_change:+d} -> {self.new_quantity}"