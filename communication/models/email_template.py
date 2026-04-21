from django.db import models
from cloudinary.models import CloudinaryField, CloudinaryResource
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User


TEMPLATE_CHOICES = (
    ("login_alert", "Login Alert"),
    ("two_factor_enabled", "Two-Factor Authentication Enabled"),
    ("two_factor_disabled", "Two-Factor Authentication Disabled"),
    ("security_alert", "Security Alert"),
)


class EmailTemplate(models.Model):

    name = models.CharField(max_length=100, choices=TEMPLATE_CHOICES, unique=True)
    subject = models.CharField(max_length=200)
    content = models.TextField(
        help_text="Use {{ subscriber.email }} for dynamic content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
