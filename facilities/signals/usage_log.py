from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from facilities.models.reservation import FacilityReservation
from .facility import Facility

class FacilityUsageLog(TimestampedModel, UUIDModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='usage_logs')
    reservation = models.ForeignKey(FacilityReservation, on_delete=models.SET_NULL, null=True, blank=True)
    used_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    condition_before = models.CharField(max_length=100, blank=True)
    condition_after = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-check_in']

    def __str__(self):
        return f"{self.facility.name} - {self.check_in.date()}"