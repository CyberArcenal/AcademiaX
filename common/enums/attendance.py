# common/enums/attendance.py
from django.db import models

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PR', 'Present'
    ABSENT = 'AB', 'Absent'
    LATE = 'LT', 'Late'
    EXCUSED = 'EX', 'Excused'
    HOLIDAY = 'HD', 'Holiday'  # no classes
    NO_CLASS = 'NC', 'No Class'  # scheduled but no session

class LateReason(models.TextChoices):
    TRAFFIC = 'TR', 'Traffic'
    PERSONAL = 'PR', 'Personal Matter'
    SICK = 'SK', 'Sick'
    OTHER = 'OT', 'Other'

class AttendanceType(models.TextChoices):
    STUDENT = 'ST', 'Student'
    TEACHER = 'TC', 'Teacher'
    STAFF = 'SF', 'Staff'  # optional