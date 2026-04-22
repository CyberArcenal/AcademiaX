from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any


from communication.models import Message
from communication.models.conversation import Conversation
from users.models import User
from common.enums.communication import MessageStatus

class MessageService:
    """Service for Message model operations"""

    @staticmethod
    def send_message(
        conversation: Conversation,
        sender: User,
        content: str
    ) -> Message:
        try:
            with transaction.atomic():
                message = Message(
                    conversation=conversation,
                    sender=sender,
                    content=content,
                    status=MessageStatus.SENT
                )
                message.full_clean()
                message.save()
                # Update conversation's last message
                from .conversation import ConversationService
                ConversationService.update_last_message(conversation, content[:100])
                return message
        except ValidationError as e:
            raise

    @staticmethod
    def get_message_by_id(message_id: int) -> Optional[Message]:
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return None

    @staticmethod
    def get_conversation_messages(conversation_id: int, limit: int = 50, before_id: Optional[int] = None) -> List[Message]:
        queryset = Message.objects.filter(conversation_id=conversation_id, is_deleted_for_all=False)
        if before_id:
            queryset = queryset.filter(id__lt=before_id)
        return queryset.order_by('-created_at')[:limit]

    @staticmethod
    def mark_as_delivered(message: Message) -> Message:
        message.status = MessageStatus.DELIVERED
        message.delivered_at = timezone.now()
        message.save()
        return message

    @staticmethod
    def mark_as_read(message: Message) -> Message:
        message.status = MessageStatus.READ
        message.read_at = timezone.now()
        message.save()
        return message

    @staticmethod
    def edit_message(message: Message, new_content: str) -> Message:
        message.content = new_content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        return message

    @staticmethod
    def delete_for_sender(message: Message) -> Message:
        message.is_deleted_for_sender = True
        message.save()
        return message

    @staticmethod
    def delete_for_all(message: Message) -> Message:
        message.is_deleted_for_all = True
        message.save()
        return message

    @staticmethod
    def delete_message(message: Message) -> bool:
        try:
            message.delete()
            return True
        except Exception:
            return False