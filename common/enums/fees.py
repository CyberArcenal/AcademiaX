# common/enums/fees.py
from django.db import models

class FeeCategory(models.TextChoices):
    TUITION = 'TUI', 'Tuition Fee'
    LABORATORY = 'LAB', 'Laboratory Fee'
    LIBRARY = 'LIB', 'Library Fee'
    COMPUTER = 'COM', 'Computer Fee'
    SPORTS = 'SPT', 'Sports Fee'
    MEDICAL = 'MED', 'Medical/Dental Fee'
    GUIDANCE = 'GUID', 'Guidance Fee'
    STUDENT_ORG = 'SO', 'Student Organization Fee'
    INSURANCE = 'INS', 'Insurance'
    OTHER = 'OTH', 'Other'

class PaymentStatus(models.TextChoices):
    PENDING = 'PND', 'Pending'
    PARTIAL = 'PRT', 'Partially Paid'
    PAID = 'PD', 'Fully Paid'
    OVERDUE = 'OVD', 'Overdue'
    CANCELLED = 'CNC', 'Cancelled'

class DiscountType(models.TextChoices):
    PERCENTAGE = 'PCT', 'Percentage'
    FIXED = 'FXD', 'Fixed Amount'

class ScholarshipType(models.TextChoices):
    ACADEMIC = 'ACD', 'Academic Scholarship'
    ATHLETIC = 'ATH', 'Athletic Scholarship'
    NEED_BASED = 'NED', 'Need-Based'
    GOVERNMENT = 'GOV', 'Government Grant'
    PRIVATE = 'PRV', 'Private Grant'

class TransactionType(models.TextChoices):
    ASSESSMENT = 'ASS', 'Assessment'
    PAYMENT = 'PAY', 'Payment'
    ADJUSTMENT = 'ADJ', 'Adjustment'
    REFUND = 'REF', 'Refund'