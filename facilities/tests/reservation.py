from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.facilities import ReservationStatus
from .facility import Facility

class FacilityReservation(TimestampedModel, UUIDModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='reservations')
    reserved_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='facility_reservations')
    title = models.CharField(max_length=200)
    purpose = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=ReservationStatus.choices, default=ReservationStatus.PENDING)
    attendees_count = models.PositiveIntegerField(default=0)
    requires_setup = models.BooleanField(default=False)
    setup_notes = models.TextField(blank=True)
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reservations')
    approved_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['facility', 'start_datetime', 'end_datetime']),
        ]

    def __str__(self):
        return f"{self.facility.name} - {self.title} ({self.start_datetime.date()})"