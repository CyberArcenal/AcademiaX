from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List

from communication.models.announcement import Announcement
from communication.models.broadcast_log import BroadcastLog
from users.models import User

class BroadcastLogService:
    """Service for BroadcastLog model operations"""

    @staticmethod
    def create_log(
        announcement: Announcement,
        recipient: User,
        channel: str,
        status: str = 'PENDING',
        error_message: str = ""
    ) -> BroadcastLog:
        try:
            with transaction.atomic():
                log = BroadcastLog(
                    announcement=announcement,
                    recipient=recipient,
                    channel=channel,
                    status=status,
                    error_message=error_message
                )
                log.full_clean()
                log.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[BroadcastLog]:
        try:
            return BroadcastLog.objects.get(id=log_id)
        except BroadcastLog.DoesNotExist:
            return None

    @staticmethod
    def get_logs_by_announcement(announcement_id: int) -> List[BroadcastLog]:
        return BroadcastLog.objects.filter(announcement_id=announcement_id)

    @staticmethod
    def update_status(log: BroadcastLog, status: str, error_message: str = "") -> BroadcastLog:
        log.status = status
        if error_message:
            log.error_message = error_message
        if status == 'SENT':
            log.sent_at = timezone.now()
        log.save()
        return log

    @staticmethod
    def get_failed_logs() -> List[BroadcastLog]:
        return BroadcastLog.objects.filter(status='FAILED')

    @staticmethod
    def retry_failed(log: BroadcastLog) -> BroadcastLog:
        log.status = 'PENDING'
        log.error_message = ""
        log.save()
        return log