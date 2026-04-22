from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.timetable import ScheduleType
from .test_time_slot import TimeSlot

class Schedule(TimestampedModel, UUIDModel, SoftDeleteModel):
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='schedules')
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='schedules')
    room = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='schedules')
    schedule_type = models.CharField(max_length=3, choices=ScheduleType.choices, default=ScheduleType.REGULAR)
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE, related_name='schedules')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['time_slot', 'section']]  # No two classes in same time for a section
        # Also ensure teacher and room not double-booked (enforced in validation, not DB)
        ordering = ['time_slot__day_of_week', 'time_slot__order']

    def __str__(self):
        return f"{self.section} - {self.subject.code} - {self.time_slot}"