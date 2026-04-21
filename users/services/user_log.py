from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any

from users.models.user import User
from users.models.user_log import UserLog


class UserLogService:
    """Service for UserLog model operations (audit trail)"""

    @staticmethod
    def create_log(
        user: User,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: str = "",
        details: Dict = None
    ) -> UserLog:
        try:
            with transaction.atomic():
                log = UserLog(
                    user=user,
                    action=action,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details=details or {},
                    created_at=timezone.now()
                )
                log.full_clean()
                log.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[UserLog]:
        try:
            return UserLog.objects.get(id=log_id)
        except UserLog.DoesNotExist:
            return None

    @staticmethod
    def get_logs_by_user(user_id: int, limit: int = 100) -> List[UserLog]:
        return UserLog.objects.filter(user_id=user_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_logs_by_action(action: str, limit: int = 100) -> List[UserLog]:
        return UserLog.objects.filter(action=action).order_by('-created_at')[:limit]

    @staticmethod
    def get_logs_by_date_range(start_date, end_date) -> List[UserLog]:
        return UserLog.objects.filter(created_at__gte=start_date, created_at__lte=end_date).order_by('-created_at')

    @staticmethod
    def delete_old_logs(days_to_keep: int = 90) -> int:
        """Delete logs older than specified days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        count, _ = UserLog.objects.filter(created_at__lt=cutoff_date).delete()
        return count