from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .message import Message

class MessageAttachment(TimestampedModel, UUIDModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file_url = models.URLField()
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.file_name