from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.canteen import PaymentMethod
from .order import Order

class PaymentTransaction(TimestampedModel, UUIDModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    reference_number = models.CharField(max_length=100, blank=True, help_text="For card/QR transactions")
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    notes = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.order.order_number} - ₱{self.amount_paid}"