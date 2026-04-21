from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .parent import Parent

class ParentCommunicationLog(TimestampedModel, UUIDModel):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='communication_logs')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=[
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('CALL', 'Phone Call'),
        ('IN_PERSON', 'In Person'),
        ('PORTAL', 'Parent Portal'),
    ])
    direction = models.CharField(max_length=10, choices=[
        ('INCOMING', 'Incoming'),
        ('OUTGOING', 'Outgoing'),
    ])
    sent_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_comms')
    follow_up_required = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Communication with {self.parent} - {self.subject}"