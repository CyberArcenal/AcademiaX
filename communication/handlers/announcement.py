from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.communication import TargetAudience, NotificationChannel

class Announcement(TimestampedModel, UUIDModel, SoftDeleteModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    target_audience = models.CharField(max_length=10, choices=TargetAudience.choices, default=TargetAudience.ALL)
    # Optional filters for specific grade level or section
    grade_level = models.ForeignKey('classes.GradeLevel', on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE, null=True, blank=True)
    channels = models.JSONField(default=list, help_text="List of channels: e.g., ['APP', 'EMAIL']")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    attachment_urls = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title