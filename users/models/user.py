from django.contrib.auth.models import AbstractUser
from django.db import models
from common.base.models import TimestampedModel
from common.enums.users import UserRole, AccountStatus
from common.utils.helpers import phone_regex

class User(AbstractUser, TimestampedModel):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    status = models.CharField(max_length=20, choices=AccountStatus.choices, default=AccountStatus.PENDING)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,  # para may allowance sa '+' at country code
        blank=True,
        help_text="Enter phone number in international format (e.g. +639171234567)"
    )
    middle_name = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(max_length=20, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.URLField(blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    force_password_change = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.middle_name} {self.last_name} {self.suffix}".strip()
        return self.username