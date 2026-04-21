from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .enrollment import Enrollment

class EnrollmentHold(TimestampedModel, UUIDModel):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='hold')
    reason = models.CharField(max_length=200)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Hold for {self.enrollment} - {self.reason[:50]}"