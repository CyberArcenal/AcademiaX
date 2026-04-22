from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.report import Report
from users.models import User
from common.enums.reports import ReportType, ReportFormat, ReportStatus

class ReportService:
    """Service for Report model operations"""

    @staticmethod
    def create_report(
        name: str,
        report_type: str,
        format: str = ReportFormat.PDF,
        parameters: Dict = None,
        generated_by: Optional[User] = None,
        expires_at: Optional[datetime] = None,
        status: str = ReportStatus.PENDING
    ) -> Report:
        try:
            with transaction.atomic():
                report = Report(
                    name=name,
                    report_type=report_type,
                    format=format,
                    parameters=parameters or {},
                    status=status,
                    generated_by=generated_by,
                    expires_at=expires_at
                )
                report.full_clean()
                report.save()
                return report
        except ValidationError as e:
            raise

    @staticmethod
    def get_report_by_id(report_id: int) -> Optional[Report]:
        try:
            return Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return None

    @staticmethod
    def get_reports_by_user(user_id: int, limit: int = 50) -> List[Report]:
        return Report.objects.filter(generated_by_id=user_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_reports_by_type(report_type: str, limit: int = 50) -> List[Report]:
        return Report.objects.filter(report_type=report_type).order_by('-created_at')[:limit]

    @staticmethod
    def get_pending_reports() -> List[Report]:
        return Report.objects.filter(status=ReportStatus.PENDING).order_by('created_at')

    @staticmethod
    def update_report(report: Report, update_data: Dict[str, Any]) -> Report:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(report, field):
                        setattr(report, field, value)
                report.full_clean()
                report.save()
                return report
        except ValidationError as e:
            raise

    @staticmethod
    def mark_completed(
        report: Report,
        file_url: str,
        file_size: Optional[int] = None
    ) -> Report:
        report.status = ReportStatus.COMPLETED
        report.file_url = file_url
        report.file_size = file_size
        report.generated_at = timezone.now()
        report.save()
        return report

    @staticmethod
    def mark_failed(report: Report, error_message: str) -> Report:
        report.status = ReportStatus.FAILED
        report.error_message = error_message
        report.save()
        return report

    @staticmethod
    def delete_report(report: Report) -> bool:
        try:
            report.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_reports_by_date_range(start_date: datetime, end_date: datetime) -> List[Report]:
        return Report.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

    @staticmethod
    def cleanup_expired_reports() -> int:
        """Delete expired reports (where expires_at is in the past)"""
        now = timezone.now()
        count, _ = Report.objects.filter(expires_at__lt=now, status=ReportStatus.COMPLETED).delete()
        return count