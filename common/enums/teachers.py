# common/enums/teachers.py
from django.db import models

class TeacherStatus(models.TextChoices):
    ACTIVE = 'ACT', 'Active'
    INACTIVE = 'INA', 'Inactive'
    ON_LEAVE = 'LV', 'On Leave'
    RESIGNED = 'RES', 'Resigned'
    TERMINATED = 'TER', 'Terminated'

class TeacherType(models.TextChoices):
    FULL_TIME = 'FT', 'Full-time'
    PART_TIME = 'PT', 'Part-time'
    VISITING = 'VS', 'Visiting'
    PRACTICUM = 'PR', 'Practicum Teacher'

class HighestDegree(models.TextChoices):
    BACHELOR = 'BS', 'Bachelor\'s Degree'
    MASTER = 'MA', 'Master\'s Degree'
    DOCTORATE = 'PHD', 'Doctorate'
    DIPLOMA = 'DIP', 'Diploma'