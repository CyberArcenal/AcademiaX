from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from .facility import Facility

class Equipment(TimestampedModel, UUIDModel, SoftDeleteModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='equipment', null=True, blank=True)
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='OPERATIONAL', choices=[
        ('OPERATIONAL', 'Operational'),
        ('NEEDS_REPAIR', 'Needs Repair'),
        ('UNDER_REPAIR', 'Under Repair'),
        ('RETIRED', 'Retired'),
    ])
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.serial_number})"