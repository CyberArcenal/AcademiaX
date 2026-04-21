from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.library import FineStatus
from .borrow import BorrowTransaction

class Fine(TimestampedModel, UUIDModel):
    borrow_transaction = models.OneToOneField(BorrowTransaction, on_delete=models.CASCADE, related_name='fine')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    days_overdue = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=FineStatus.choices, default=FineStatus.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Fine for {self.borrow_transaction}: {self.amount}"