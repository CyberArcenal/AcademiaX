from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel
from common.enums.communication import MessageStatus
from .conversation import Conversation

class Message(TimestampedModel, UUIDModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    status = models.CharField(max_length=10, choices=MessageStatus.choices, default=MessageStatus.SENT)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted_for_sender = models.BooleanField(default=False)
    is_deleted_for_all = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"