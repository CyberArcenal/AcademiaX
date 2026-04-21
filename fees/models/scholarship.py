from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.fees import ScholarshipType
from .discount import Discount

class Scholarship(TimestampedModel, UUIDModel, SoftDeleteModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='scholarships')
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='scholarships')
    scholarship_type = models.CharField(max_length=10, choices=ScholarshipType.choices)
    grantor = models.CharField(max_length=200, blank=True, help_text="Organization or donor")
    awarded_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_renewable = models.BooleanField(default=False)
    terms = models.TextField(blank=True)
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = [['student', 'discount', 'awarded_date']]

    def __str__(self):
        return f"{self.student} - {self.discount.name}"