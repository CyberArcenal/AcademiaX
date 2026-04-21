from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from django.utils import timezone
from ..models.conversation import Conversation
from ...users.models import User
from ...common.enums.communication import ConversationType

class ConversationService:
    """Service for Conversation model operations"""

    @staticmethod
    def create_conversation(
        participants: List[User],
        created_by: User,
        conversation_type: str = ConversationType.ONE_ON_ONE,
        name: str = ""
    ) -> Conversation:
        try:
            with transaction.atomic():
                if conversation_type == ConversationType.ONE_ON_ONE and len(participants) != 2:
                    raise ValidationError("One-to-one conversation requires exactly 2 participants")

                conversation = Conversation(
                    conversation_type=conversation_type,
                    name=name if conversation_type == ConversationType.GROUP else "",
                    created_by=created_by
                )
                conversation.full_clean()
                conversation.save()
                conversation.participants.set(participants)
                return conversation
        except ValidationError as e:
            raise

    @staticmethod
    def get_conversation_by_id(conversation_id: int) -> Optional[Conversation]:
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    @staticmethod
    def get_user_conversations(user_id: int) -> List[Conversation]:
        return Conversation.objects.filter(participants__id=user_id, is_active=True)

    @staticmethod
    def get_or_create_private_conversation(user1: User, user2: User) -> Conversation:
        """Get existing private conversation between two users or create new"""
        conversation = Conversation.objects.filter(
            conversation_type=ConversationType.ONE_ON_ONE,
            participants=user1
        ).filter(participants=user2).first()
        if conversation:
            return conversation
        return ConversationService.create_conversation(
            participants=[user1, user2],
            created_by=user1,
            conversation_type=ConversationType.ONE_ON_ONE
        )

    @staticmethod
    def add_participant(conversation: Conversation, user: User) -> Conversation:
        if conversation.conversation_type != ConversationType.GROUP:
            raise ValidationError("Only group conversations can have multiple participants")
        conversation.participants.add(user)
        return conversation

    @staticmethod
    def remove_participant(conversation: Conversation, user: User) -> Conversation:
        conversation.participants.remove(user)
        return conversation

    @staticmethod
    def update_last_message(conversation: Conversation, last_message: str) -> Conversation:
        conversation.last_message = last_message
        conversation.last_message_at = timezone.now()
        conversation.save()
        return conversation

    @staticmethod
    def delete_conversation(conversation: Conversation, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                conversation.is_active = False
                conversation.save()
            else:
                conversation.delete()
            return True
        except Exception:
            return False