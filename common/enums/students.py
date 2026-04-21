# common/enums/students.py
from django.db import models

class StudentStatus(models.TextChoices):
    ACTIVE = 'ACT', 'Active'
    INACTIVE = 'INA', 'Inactive'
    TRANSFERRED = 'TRF', 'Transferred'
    GRADUATED = 'GRD', 'Graduated'
    DROPPED = 'DRP', 'Dropped'
    ON_LEAVE = 'LV', 'On Leave'

class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'

class BloodType(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'
    UNKNOWN = 'UNK', 'Unknown'