from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.report_log import ReportLog
from ..models.report import Report
from users.models import User

class ReportLogService:
    """Service for ReportLog model operations"""

    @staticmethod
    def create_log(
        report: Report,
        action: str,
        performed_by: Optional[User] = None,
        ip_address: Optional[str] = None,
        user_agent: str = "",
        details: Dict = None
    ) -> ReportLog:
        try:
            with transaction.atomic():
                log = ReportLog(
                    report=report,
                    action=action,
                    performed_by=performed_by,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details=details or {}
                )
                log.full_clean()
                log.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[ReportLog]:
        try:
            return ReportLog.objects.get(id=log_id)
        except ReportLog.DoesNotExist:
            return None

    @staticmethod
    def get_logs_by_report(report_id: int, limit: int = 50) -> List[ReportLog]:
        return ReportLog.objects.filter(report_id=report_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_logs_by_action(action: str, limit: int = 100) -> List[ReportLog]:
        return ReportLog.objects.filter(action=action).order_by('-created_at')[:limit]

    @staticmethod
    def delete_log(log: ReportLog) -> bool:
        try:
            log.delete()
            return True
        except Exception:
            return False