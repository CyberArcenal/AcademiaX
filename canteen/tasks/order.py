from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel
from common.enums.canteen import OrderStatus, OrderType

class Order(TimestampedModel, UUIDModel):
    # Customer can be student, teacher, or staff
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='canteen_orders'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='canteen_orders'
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    order_type = models.CharField(max_length=10, choices=OrderType.choices, default=OrderType.DINE_IN)
    status = models.CharField(max_length=10, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    prepared_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prepared_orders'
    )
    served_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        customer = self.student or self.user
        return f"Order {self.order_number} - {customer}"