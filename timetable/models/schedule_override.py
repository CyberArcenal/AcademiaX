from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .test_schedule import Schedule

class ScheduleOverride(TimestampedModel, UUIDModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='overrides')
    date = models.DateField()
    new_start_time = models.TimeField(null=True, blank=True)
    new_end_time = models.TimeField(null=True, blank=True)
    new_room = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True)
    new_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=200)
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        unique_together = [['schedule', 'date']]

    def __str__(self):
        return f"Override for {self.schedule} on {self.date}"