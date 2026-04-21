import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationStateTransitionService:
    """Handles side effects of notification state changes."""

    @staticmethod
    def handle_creation(notification):
        """When a new notification is created, maybe send real-time via WebSocket."""
        # Placeholder for WebSocket push
        logger.info(f"Notification {notification.id} created for user {notification.recipient.id}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'is_read' in changes:
            NotificationStateTransitionService._handle_read_change(
                instance, changes['is_read']['old'], changes['is_read']['new']
            )

    @staticmethod
    def _handle_read_change(notification, old_value, new_value):
        """When notification is marked as read, set read_at timestamp."""
        if new_value is True and old_value is False:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])
            logger.info(f"Notification {notification.id} marked as read at {notification.read_at}")