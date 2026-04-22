from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import datetime

from facilities.models.facility import Facility
from facilities.models.reservation import FacilityReservation
from facilities.models.usage_log import FacilityUsageLog
from users.models import User

class FacilityUsageLogService:
    """Service for FacilityUsageLog model operations"""

    @staticmethod
    def create_usage_log(
        facility: Facility,
        used_by: User,
        check_in: datetime,
        reservation: Optional[FacilityReservation] = None,
        check_out: Optional[datetime] = None,
        condition_before: str = "",
        condition_after: str = "",
        notes: str = ""
    ) -> FacilityUsageLog:
        try:
            with transaction.atomic():
                log = FacilityUsageLog(
                    facility=facility,
                    reservation=reservation,
                    used_by=used_by,
                    check_in=check_in,
                    check_out=check_out,
                    condition_before=condition_before,
                    condition_after=condition_after,
                    notes=notes
                )
                log.full_clean()
                log.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[FacilityUsageLog]:
        try:
            return FacilityUsageLog.objects.get(id=log_id)
        except FacilityUsageLog.DoesNotExist:
            return None

    @staticmethod
    def get_logs_by_facility(facility_id: int, limit: int = 50) -> List[FacilityUsageLog]:
        return FacilityUsageLog.objects.filter(facility_id=facility_id).order_by('-check_in')[:limit]

    @staticmethod
    def get_logs_by_reservation(reservation_id: int) -> List[FacilityUsageLog]:
        return FacilityUsageLog.objects.filter(reservation_id=reservation_id).order_by('check_in')

    @staticmethod
    def update_log(log: FacilityUsageLog, update_data: Dict[str, Any]) -> FacilityUsageLog:
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
    def check_out(log: FacilityUsageLog, condition_after: str = "", notes: str = "") -> FacilityUsageLog:
        log.check_out = timezone.now()
        log.condition_after = condition_after
        log.notes = notes
        log.save()
        return log

    @staticmethod
    def delete_log(log: FacilityUsageLog) -> bool:
        try:
            log.delete()
            return True
        except Exception:
            return False