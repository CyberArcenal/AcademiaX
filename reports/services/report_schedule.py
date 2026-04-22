from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any

from ..models.report_schedule import ReportSchedule
from users.models import User
from common.enums.reports import ReportType, ReportFormat, ReportStatus

class ReportScheduleService:
    """Service for ReportSchedule model operations"""

    @staticmethod
    def create_schedule(
        name: str,
        report_type: str,
        cron_expression: str,
        recipients: List[str],
        format: str = ReportFormat.PDF,
        parameters: Dict = None,
        is_active: bool = True,
        created_by: Optional[User] = None
    ) -> ReportSchedule:
        try:
            with transaction.atomic():
                schedule = ReportSchedule(
                    name=name,
                    report_type=report_type,
                    format=format,
                    parameters=parameters or {},
                    cron_expression=cron_expression,
                    recipients=recipients,
                    is_active=is_active,
                    created_by=created_by
                )
                schedule.full_clean()
                schedule.save()
                return schedule
        except ValidationError as e:
            raise

    @staticmethod
    def get_schedule_by_id(schedule_id: int) -> Optional[ReportSchedule]:
        try:
            return ReportSchedule.objects.get(id=schedule_id)
        except ReportSchedule.DoesNotExist:
            return None

    @staticmethod
    def get_active_schedules() -> List[ReportSchedule]:
        return ReportSchedule.objects.filter(is_active=True)

    @staticmethod
    def update_schedule(schedule: ReportSchedule, update_data: Dict[str, Any]) -> ReportSchedule:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(schedule, field):
                        setattr(schedule, field, value)
                schedule.full_clean()
                schedule.save()
                return schedule
        except ValidationError as e:
            raise

    @staticmethod
    def delete_schedule(schedule: ReportSchedule) -> bool:
        try:
            schedule.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def update_last_run(schedule: ReportSchedule, status: str) -> ReportSchedule:
        schedule.last_run_at = timezone.now()
        schedule.last_run_status = status
        schedule.save()
        return schedule

    @staticmethod
    def get_schedules_due() -> List[ReportSchedule]:
        """Get schedules that should run based on cron expression (simplified - would need cron parser)"""
        # This is a placeholder; actual implementation would use a library like croniter
        return ReportSchedule.objects.filter(is_active=True)