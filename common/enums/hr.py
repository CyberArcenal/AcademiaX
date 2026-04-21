# common/enums/hr.py
from django.db import models

class EmploymentType(models.TextChoices):
    FULL_TIME = 'FT', 'Full-time'
    PART_TIME = 'PT', 'Part-time'
    CONTRACTUAL = 'CT', 'Contractual'
    PROBATIONARY = 'PB', 'Probationary'
    PERMANENT = 'PM', 'Permanent'
    CASUAL = 'CS', 'Casual'

class EmploymentStatus(models.TextChoices):
    ACTIVE = 'ACT', 'Active'
    RESIGNED = 'RES', 'Resigned'
    TERMINATED = 'TER', 'Terminated'
    RETIRED = 'RET', 'Retired'
    ON_LEAVE = 'LV', 'On Leave'
    SUSPENDED = 'SUS', 'Suspended'

class LeaveType(models.TextChoices):
    SICK = 'SK', 'Sick Leave'
    VACATION = 'VC', 'Vacation Leave'
    EMERGENCY = 'EM', 'Emergency Leave'
    MATERNITY = 'MT', 'Maternity Leave'
    PATERNITY = 'PT', 'Paternity Leave'
    BEREAVEMENT = 'BR', 'Bereavement Leave'
    UNPAID = 'UP', 'Unpaid Leave'

class LeaveStatus(models.TextChoices):
    PENDING = 'PND', 'Pending'
    APPROVED = 'APP', 'Approved'
    REJECTED = 'REJ', 'Rejected'
    CANCELLED = 'CNC', 'Cancelled'

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PR', 'Present'
    ABSENT = 'AB', 'Absent'
    LATE = 'LT', 'Late'
    HALF_DAY = 'HD', 'Half Day'
    ON_LEAVE = 'LV', 'On Leave'
    HOLIDAY = 'HL', 'Holiday'