from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel

class Alumni(TimestampedModel, UUIDModel, SoftDeleteModel):
    # Link to the original student record (when student graduates)
    student = models.OneToOneField(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alumni_record'
    )
    # Also link to User for authentication (alumni can log in to portal)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alumni_profile'
    )
    # Alumni-specific fields
    graduation_year = models.IntegerField(help_text="Year of graduation")
    batch = models.CharField(max_length=20, blank=True, help_text="e.g., Batch 2020")
    current_city = models.CharField(max_length=100, blank=True)
    current_country = models.CharField(max_length=100, default='Philippines')
    contact_number = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True, help_text="Personal email (not school email)")
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether alumni engages with the school")

    class Meta:
        ordering = ['-graduation_year', 'student__last_name']
        indexes = [
            models.Index(fields=['graduation_year']),
            models.Index(fields=['batch']),
        ]

    def __str__(self):
        if self.student:
            return f"{self.student.get_full_name()} - {self.graduation_year}"
        elif self.user:
            return f"{self.user.get_full_name()} - {self.graduation_year}"
        return f"Alumni {self.id} - {self.graduation_year}"