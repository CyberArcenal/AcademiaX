from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List

from ..models.attachment import MessageAttachment
from ..models.message import Message
from ...users.models import User

class MessageAttachmentService:
    """Service for MessageAttachment model operations"""

    @staticmethod
    def create_attachment(
        message: Message,
        file_url: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        uploaded_by: User
    ) -> MessageAttachment:
        try:
            with transaction.atomic():
                attachment = MessageAttachment(
                    message=message,
                    file_url=file_url,
                    file_name=file_name,
                    file_size=file_size,
                    mime_type=mime_type,
                    uploaded_by=uploaded_by
                )
                attachment.full_clean()
                attachment.save()
                return attachment
        except ValidationError as e:
            raise

    @staticmethod
    def get_attachment_by_id(attachment_id: int) -> Optional[MessageAttachment]:
        try:
            return MessageAttachment.objects.get(id=attachment_id)
        except MessageAttachment.DoesNotExist:
            return None

    @staticmethod
    def get_attachments_by_message(message_id: int) -> List[MessageAttachment]:
        return MessageAttachment.objects.filter(message_id=message_id)

    @staticmethod
    def delete_attachment(attachment: MessageAttachment) -> bool:
        try:
            attachment.delete()
            return True
        except Exception:
            return False