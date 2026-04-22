# common/enums/classes.py
from django.db import models

class TermType(models.TextChoices):
    SEMESTER = 'SEM', 'Semester'
    QUARTER = 'QTR', 'Quarter'
    TRIMESTER = 'TRI', 'Trimester'

class RoomType(models.TextChoices):
    CLASSROOM = 'CR', 'Regular Classroom'
    LABORATORY = 'LB', 'Laboratory'
    AUDITORIUM = 'AD', 'Auditorium'
    GYM = 'GY', 'Gymnasium'
    LIBRARY = 'LR', 'Library'
    OFFICE = 'OF', 'Office'