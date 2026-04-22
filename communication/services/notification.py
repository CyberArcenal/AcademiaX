from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any


from communication.models.notification import Notification
from users.models import User
from common.enums.communication import NotificationType, NotificationChannel

class NotificationService:
    """Service for Notification model operations"""

    @staticmethod
    def create_notification(
        recipient: User,
        title: str,
        message: str,
        notification_type: str = NotificationType.INFO,
        channel: str = NotificationChannel.IN_APP,
        action_url: str = "",
        metadata: Dict = None
    ) -> Notification:
        try:
            with transaction.atomic():
                notification = Notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    channel=channel,
                    action_url=action_url,
                    metadata=metadata or {}
                )
                notification.full_clean()
                notification.save()
                return notification
        except ValidationError as e:
            raise

    @staticmethod
    def get_notification_by_id(notification_id: int) -> Optional[Notification]:
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None

    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        queryset = Notification.objects.filter(recipient_id=user_id)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset.order_by('-created_at')[:limit]

    @staticmethod
    def mark_as_read(notification: Notification) -> Notification:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return notification

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        count = Notification.objects.filter(recipient_id=user_id, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return count

    @staticmethod
    def delete_notification(notification: Notification) -> bool:
        try:
            notification.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        return Notification.objects.filter(recipient_id=user_id, is_read=False).count()

    @staticmethod
    def bulk_create_notifications(recipients: List[User], title: str, message: str, **kwargs) -> List[Notification]:
        notifications = []
        with transaction.atomic():
            for recipient in recipients:
                notif = Notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    **kwargs
                )
                notif.full_clean()
                notif.save()
                notifications.append(notif)
        return notifications