from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.communication import NotificationChannel
from .announcement import Announcement
from django.conf import settings

class BroadcastLog(TimestampedModel, UUIDModel):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='broadcast_logs')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ])
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.announcement.title} -> {self.recipient} ({self.channel})"