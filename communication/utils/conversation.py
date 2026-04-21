from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.communication import ConversationType

class Conversation(TimestampedModel, UUIDModel, SoftDeleteModel):
    conversation_type = models.CharField(max_length=10, choices=ConversationType.choices, default=ConversationType.ONE_ON_ONE)
    name = models.CharField(max_length=100, blank=True, help_text="For group conversations")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_conversations')
    last_message = models.TextField(blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        if self.conversation_type == 'GRP':
            return self.name or f"Group {self.id}"
        return f"Chat between {', '.join([str(p) for p in self.participants.all()])}"