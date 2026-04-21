# common/enums/library.py
from django.db import models

class BookStatus(models.TextChoices):
    AVAILABLE = 'AVL', 'Available'
    BORROWED = 'BRW', 'Borrowed'
    RESERVED = 'RSV', 'Reserved'
    LOST = 'LST', 'Lost'
    DAMAGED = 'DMG', 'Damaged'
    UNDER_MAINTENANCE = 'MNT', 'Under Maintenance'
    WITHDRAWN = 'WTH', 'Withdrawn'

class BorrowStatus(models.TextChoices):
    PENDING = 'PND', 'Pending Approval'
    APPROVED = 'APP', 'Approved'
    BORROWED = 'BRW', 'Borrowed'
    RETURNED = 'RTN', 'Returned'
    OVERDUE = 'OVD', 'Overdue'
    CANCELLED = 'CNC', 'Cancelled'

class FineStatus(models.TextChoices):
    PENDING = 'PND', 'Pending'
    PAID = 'PD', 'Paid'
    WAIVED = 'WVD', 'Waived'