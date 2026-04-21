from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .payment import Payment

class CollectionReport(TimestampedModel, UUIDModel):
    report_date = models.DateField()
    total_collections = models.DecimalField(max_digits=15, decimal_places=2)
    total_assessments = models.DecimalField(max_digits=15, decimal_places=2)
    total_outstanding = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method_breakdown = models.JSONField(default=dict)
    generated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['report_date']]
        ordering = ['-report_date']

    def __str__(self):
        return f"Collection Report - {self.report_date}"