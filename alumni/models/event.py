from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.alumni import RSVPStatus
from .alumni import Alumni

class AlumniEvent(TimestampedModel, UUIDModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    registration_deadline = models.DateTimeField()

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return f"{self.title} - {self.event_date.date()}"

class EventAttendance(TimestampedModel, UUIDModel):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='event_attendances')
    event = models.ForeignKey(AlumniEvent, on_delete=models.CASCADE, related_name='attendances')
    rsvp_status = models.CharField(max_length=10, choices=RSVPStatus.choices, default=RSVPStatus.NO_RESPONSE)
    attended = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['alumni', 'event']]

    def __str__(self):
        return f"{self.alumni} - {self.event.title} ({self.get_rsvp_status_display()})"