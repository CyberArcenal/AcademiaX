# common/enums/communication.py
from django.db import models

class NotificationType(models.TextChoices):
    INFO = 'INFO', 'Information'
    WARNING = 'WARN', 'Warning'
    ALERT = 'ALRT', 'Alert'
    REMINDER = 'REM', 'Reminder'
    GRADE_RELEASED = 'GRADE', 'Grade Released'
    ATTENDANCE = 'ATT', 'Attendance Alert'
    PAYMENT = 'PAY', 'Payment Reminder'
    EVENT = 'EVT', 'Event'

class NotificationChannel(models.TextChoices):
    IN_APP = 'APP', 'In-App'
    EMAIL = 'EML', 'Email'
    SMS = 'SMS', 'SMS'
    PUSH = 'PUSH', 'Push Notification'

class MessageStatus(models.TextChoices):
    SENT = 'SENT', 'Sent'
    DELIVERED = 'DEL', 'Delivered'
    READ = 'READ', 'Read'
    FAILED = 'FAIL', 'Failed'

class ConversationType(models.TextChoices):
    ONE_ON_ONE = 'P2P', 'One-to-One'
    GROUP = 'GRP', 'Group'
    BROADCAST = 'BRD', 'Broadcast'

class TargetAudience(models.TextChoices):
    ALL = 'ALL', 'Everyone'
    STUDENTS = 'STU', 'Students Only'
    TEACHERS = 'TCH', 'Teachers Only'
    STAFF = 'STF', 'Staff Only'
    PARENTS = 'PAR', 'Parents Only'
    GRADE_LEVEL = 'GRD', 'Specific Grade Level'
    SECTION = 'SEC', 'Specific Section'