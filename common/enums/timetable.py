# common/enums/timetable.py
from django.db import models

class DayOfWeek(models.TextChoices):
    MONDAY = 'MON', 'Monday'
    TUESDAY = 'TUE', 'Tuesday'
    WEDNESDAY = 'WED', 'Wednesday'
    THURSDAY = 'THU', 'Thursday'
    FRIDAY = 'FRI', 'Friday'
    SATURDAY = 'SAT', 'Saturday'
    SUNDAY = 'SUN', 'Sunday'

class ScheduleType(models.TextChoices):
    REGULAR = 'REG', 'Regular Class'
    EXAM = 'EXM', 'Examination'
    SPECIAL = 'SPC', 'Special Event'
    CANCELLED = 'CNL', 'Cancelled'