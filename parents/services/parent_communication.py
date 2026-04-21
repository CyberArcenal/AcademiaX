from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.parent_communication import ParentCommunicationLog
from ..models.parent import Parent
from ...users.models import User

class ParentCommunicationLogService:
    """Service for ParentCommunicationLog model operations"""

    @staticmethod
    def create_log(
        parent: Parent,
        subject: str,
        message: str,
        channel: str,
        direction: str,
        sent_by: Optional[User] = None,
        follow_up_required: bool = False
    ) -> ParentCommunicationLog:
        try:
            with transaction.atomic():
                log = ParentCommunicationLog(
                    parent=parent,
                    subject=subject,
                    message=message,
                    channel=channel,
                    direction=direction,
                    sent_by=sent_by,
                    is_resolved=False,
                    follow_up_required=follow_up_required
                )
                log.full_clean()
                log.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[ParentCommunicationLog]:
        try:
            return ParentCommunicationLog.objects.get(id=log_id)
        except ParentCommunicationLog.DoesNotExist:
            return None

    @staticmethod
    def get_logs_by_parent(parent_id: int, limit: int = 50) -> List[ParentCommunicationLog]:
        return ParentCommunicationLog.objects.filter(parent_id=parent_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_unresolved_logs() -> List[ParentCommunicationLog]:
        return ParentCommunicationLog.objects.filter(is_resolved=False).order_by('-created_at')

    @staticmethod
    def update_log(log: ParentCommunicationLog, update_data: Dict[str, Any]) -> ParentCommunicationLog:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(log, field):
                        setattr(log, field, value)
                log.full_clean()
                log.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def resolve_log(log: ParentCommunicationLog, resolved_by: User, resolution_notes: str = "") -> ParentCommunicationLog:
        log.is_resolved = True
        log.resolved_at = datetime.now()
        log.resolved_by = resolved_by
        if resolution_notes:
            log.message += f"\n[Resolution: {resolution_notes}]"
        log.save()
        return log

    @staticmethod
    def delete_log(log: ParentCommunicationLog) -> bool:
        try:
            log.delete()
            return True
        except Exception:
            return False