# common/enums/enrollment.py
from django.db import models

class EnrollmentStatus(models.TextChoices):
    PENDING = 'PND', 'Pending Approval'
    ENROLLED = 'ENR', 'Enrolled'
    DROPPED = 'DRP', 'Dropped'
    TRANSFERRED = 'TRF', 'Transferred'
    GRADUATED = 'GRD', 'Graduated'
    WITHDRAWN = 'WDN', 'Withdrawn'
    ON_LEAVE = 'LV', 'On Leave'
    SUSPENDED = 'SUS', 'Suspended'

class DropReason(models.TextChoices):
    FINANCIAL = 'FIN', 'Financial'
    ACADEMIC = 'ACD', 'Academic Difficulty'
    PERSONAL = 'PRS', 'Personal'
    TRANSFER = 'TRF', 'Transfer to Another School'
    HEALTH = 'HLT', 'Health'
    OTHER = 'OTH', 'Other'

class EnrollmentPaymentStatus(models.TextChoices):
    UNPAID = 'UNP', 'Unpaid'
    PARTIAL = 'PRT', 'Partially Paid'
    PAID = 'PD', 'Fully Paid'
    SCHOLARSHIP = 'SCH', 'Covered by Scholarship'