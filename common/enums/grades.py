# common/enums/grades.py
from django.db import models

class GradeStatus(models.TextChoices):
    DRAFT = 'DRF', 'Draft'
    SUBMITTED = 'SUB', 'Submitted'
    APPROVED = 'APP', 'Approved'
    POSTED = 'PST', 'Posted'

class GradeScale(models.TextChoices):
    NUMERIC = 'NUM', 'Numeric (0-100)'
    LETTER = 'LET', 'Letter Grade (A-F)'
    DESCRIPTIVE = 'DES', 'Descriptive (Excellent, Good, etc.)'

class Quarter(models.TextChoices):
    Q1 = 'Q1', '1st Quarter'
    Q2 = 'Q2', '2nd Quarter'
    Q3 = 'Q3', '3rd Quarter'
    Q4 = 'Q4', '4th Quarter'