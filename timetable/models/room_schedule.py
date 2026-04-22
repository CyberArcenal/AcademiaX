from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .test_time_slot import TimeSlot
from facilities.models import Facility

class RoomSchedule(TimestampedModel, UUIDModel):
    room = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='room_schedules')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='room_schedules')
    event_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    recurring_end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [['room', 'time_slot', 'date']]

    def __str__(self):
        return f"{self.room.name} - {self.event_name} on {self.date}"