from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date, time

from ..models.schedule_override import ScheduleOverride
from ..models.schedule import Schedule
from ...facilities.models.facility import Facility
from ...teachers.models.teacher import Teacher

class ScheduleOverrideService:
    """Service for ScheduleOverride model operations"""

    @staticmethod
    def create_override(
        schedule: Schedule,
        date: date,
        new_start_time: Optional[time] = None,
        new_end_time: Optional[time] = None,
        new_room: Optional[Facility] = None,
        new_teacher: Optional[Teacher] = None,
        reason: str = "",
        is_cancelled: bool = False
    ) -> ScheduleOverride:
        try:
            with transaction.atomic():
                # Check if override already exists for this schedule and date
                existing = ScheduleOverride.objects.filter(schedule=schedule, date=date).first()
                if existing:
                    raise ValidationError("Override already exists for this schedule and date")

                # Validate time if provided
                if new_start_time and new_end_time and new_start_time >= new_end_time:
                    raise ValidationError("Start time must be before end time")

                override = ScheduleOverride(
                    schedule=schedule,
                    date=date,
                    new_start_time=new_start_time,
                    new_end_time=new_end_time,
                    new_room=new_room,
                    new_teacher=new_teacher,
                    reason=reason,
                    is_cancelled=is_cancelled
                )
                override.full_clean()
                override.save()
                return override
        except ValidationError as e:
            raise

    @staticmethod
    def get_override_by_id(override_id: int) -> Optional[ScheduleOverride]:
        try:
            return ScheduleOverride.objects.get(id=override_id)
        except ScheduleOverride.DoesNotExist:
            return None

    @staticmethod
    def get_overrides_by_schedule(schedule_id: int) -> List[ScheduleOverride]:
        return ScheduleOverride.objects.filter(schedule_id=schedule_id).order_by('date')

    @staticmethod
    def get_overrides_by_date(date: date) -> List[ScheduleOverride]:
        return ScheduleOverride.objects.filter(date=date).select_related('schedule')

    @staticmethod
    def update_override(override: ScheduleOverride, update_data: Dict[str, Any]) -> ScheduleOverride:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(override, field):
                        setattr(override, field, value)
                if 'new_start_time' in update_data and 'new_end_time' in update_data:
                    if override.new_start_time and override.new_end_time and override.new_start_time >= override.new_end_time:
                        raise ValidationError("Start time must be before end time")
                override.full_clean()
                override.save()
                return override
        except ValidationError as e:
            raise

    @staticmethod
    def delete_override(override: ScheduleOverride) -> bool:
        try:
            override.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def cancel_override(override: ScheduleOverride) -> ScheduleOverride:
        override.is_cancelled = True
        override.save()
        return override