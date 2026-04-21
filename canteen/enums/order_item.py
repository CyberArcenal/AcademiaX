from django.db import models
from common.base.models import TimestampedModel
from .order import Order
from .product import Product

class OrderItem(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    special_instructions = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} x{self.quantity}"