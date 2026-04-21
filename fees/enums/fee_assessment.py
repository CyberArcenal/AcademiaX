from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.fees import PaymentStatus
from .fee_structure import FeeStructure

class FeeAssessment(TimestampedModel, UUIDModel, SoftDeleteModel):
    enrollment = models.ForeignKey('enrollments.Enrollment', on_delete=models.CASCADE, related_name='fee_assessments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='assessments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE, related_name='fee_assessments', null=True, blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = [['enrollment', 'fee_structure', 'term']]
        ordering = ['due_date']

    def __str__(self):
        return f"{self.enrollment} - {self.fee_structure.name} - {self.amount}"