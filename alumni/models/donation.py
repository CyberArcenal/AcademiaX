from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.alumni import DonationPurpose
from .alumni import Alumni

class Donation(TimestampedModel, UUIDModel):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.CharField(max_length=10, choices=DonationPurpose.choices, default=DonationPurpose.GENERAL)
    date = models.DateField()
    receipt_number = models.CharField(max_length=50, blank=True)
    is_anonymous = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.alumni} - {self.amount} on {self.date}"