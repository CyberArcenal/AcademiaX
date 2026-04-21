from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from django.conf import settings

class Wallet(TimestampedModel, UUIDModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='canteen_wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user} - ₱{self.balance}"

class WalletTransaction(TimestampedModel, UUIDModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('LOAD', 'Load'), ('DEDUCT', 'Deduct')])
    reference = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user} - {self.transaction_type}: ₱{self.amount}"