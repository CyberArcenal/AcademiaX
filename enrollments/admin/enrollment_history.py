from django.db import models
from common.base.models import TimestampedModel
from .enrollment import Enrollment
from common.enums.enrollment import EnrollmentStatus, DropReason

class EnrollmentHistory(TimestampedModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='history')
    previous_status = models.CharField(max_length=10, choices=EnrollmentStatus.choices)
    new_status = models.CharField(max_length=10, choices=EnrollmentStatus.choices)
    reason = models.CharField(max_length=10, choices=DropReason.choices, blank=True, null=True)
    remarks = models.TextField(blank=True)
    changed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.enrollment} - {self.previous_status} -> {self.new_status}"