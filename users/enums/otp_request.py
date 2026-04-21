
from enum import Enum
from django.db import models

class OtpRequestType(models.TextChoices):
    """Enum for OTP request types."""
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"