from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.parents import ParentStatus

class Parent(TimestampedModel, UUIDModel, SoftDeleteModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_profile'
    )
    status = models.CharField(max_length=10, choices=ParentStatus.choices, default=ParentStatus.ACTIVE)
    contact_number = models.CharField(max_length=20, blank=True)
    alternative_contact = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, help_text="Personal email (different from user email)")
    occupation = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=200, blank=True)
    employer_address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(max_length=50, default='English')
    receive_notifications = models.BooleanField(default=True)
    receive_email_digest = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()}"