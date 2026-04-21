from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.fees import TransactionType
from .fee_assessment import FeeAssessment

class Payment(TimestampedModel, UUIDModel):
    assessment = models.ForeignKey(FeeAssessment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    reference_number = models.CharField(max_length=100, unique=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('ONLINE', 'Online Payment'),
        ('CARD', 'Debit/Credit Card'),
    ])
    check_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='received_payments')
    notes = models.TextField(blank=True)
    is_verified = models.BooleanField(default=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.reference_number} - {self.amount}"