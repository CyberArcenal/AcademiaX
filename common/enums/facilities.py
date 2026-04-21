# common/enums/facilities.py
from django.db import models

class FacilityType(models.TextChoices):
    BUILDING = 'BLD', 'Building'
    CLASSROOM = 'CR', 'Classroom'
    LABORATORY = 'LAB', 'Laboratory'
    LIBRARY = 'LIB', 'Library'
    AUDITORIUM = 'AUD', 'Auditorium'
    GYM = 'GYM', 'Gymnasium'
    OFFICE = 'OFF', 'Office'
    CANTEEN = 'CAN', 'Canteen'
    RESTROOM = 'RST', 'Restroom'
    PARKING = 'PRK', 'Parking'
    FIELD = 'FLD', 'Sports Field'

class FacilityStatus(models.TextChoices):
    AVAILABLE = 'AVL', 'Available'
    OCCUPIED = 'OCC', 'Occupied'
    UNDER_MAINTENANCE = 'MNT', 'Under Maintenance'
    RESERVED = 'RSV', 'Reserved'
    CLOSED = 'CLS', 'Closed'

class MaintenancePriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MED', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URG', 'Urgent'

class MaintenanceStatus(models.TextChoices):
    PENDING = 'PND', 'Pending'
    IN_PROGRESS = 'INP', 'In Progress'
    COMPLETED = 'CMP', 'Completed'
    CANCELLED = 'CNC', 'Cancelled'

class ReservationStatus(models.TextChoices):
    PENDING = 'PND', 'Pending Approval'
    APPROVED = 'APP', 'Approved'
    REJECTED = 'REJ', 'Rejected'
    CANCELLED = 'CNC', 'Cancelled'
    COMPLETED = 'CMP', 'Completed'