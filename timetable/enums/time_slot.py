from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.timetable import DayOfWeek

class TimeSlot(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=50, help_text="e.g., 1st Period, Homeroom")
    day_of_week = models.CharField(max_length=3, choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveSmallIntegerField(help_text="Sequence for the day")
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE, related_name='time_slots')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['academic_year', 'day_of_week', 'order']]
        ordering = ['academic_year', 'day_of_week', 'order']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.order}: {self.start_time}-{self.end_time}"