from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import time

from ..models.test_time_slot import TimeSlot
from ...classes.models.academic_year import AcademicYear
from ...common.enums.timetable import DayOfWeek

class TimeSlotService:
    """Service for TimeSlot model operations"""

    @staticmethod
    def create_time_slot(
        name: str,
        day_of_week: str,
        start_time: time,
        end_time: time,
        order: int,
        academic_year: AcademicYear,
        is_active: bool = True
    ) -> TimeSlot:
        try:
            with transaction.atomic():
                if start_time >= end_time:
                    raise ValidationError("Start time must be before end time")

                time_slot = TimeSlot(
                    name=name,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    order=order,
                    academic_year=academic_year,
                    is_active=is_active
                )
                time_slot.full_clean()
                time_slot.save()
                return time_slot
        except ValidationError as e:
            raise

    @staticmethod
    def get_time_slot_by_id(slot_id: int) -> Optional[TimeSlot]:
        try:
            return TimeSlot.objects.get(id=slot_id)
        except TimeSlot.DoesNotExist:
            return None

    @staticmethod
    def get_time_slots_by_academic_year(academic_year_id: int, active_only: bool = True) -> List[TimeSlot]:
        queryset = TimeSlot.objects.filter(academic_year_id=academic_year_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('day_of_week', 'order')

    @staticmethod
    def get_time_slots_by_day(academic_year_id: int, day: str) -> List[TimeSlot]:
        return TimeSlot.objects.filter(
            academic_year_id=academic_year_id,
            day_of_week=day,
            is_active=True
        ).order_by('order')

    @staticmethod
    def update_time_slot(time_slot: TimeSlot, update_data: Dict[str, Any]) -> TimeSlot:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(time_slot, field):
                        setattr(time_slot, field, value)
                if 'start_time' in update_data and 'end_time' in update_data:
                    if time_slot.start_time >= time_slot.end_time:
                        raise ValidationError("Start time must be before end time")
                time_slot.full_clean()
                time_slot.save()
                return time_slot
        except ValidationError as e:
            raise

    @staticmethod
    def delete_time_slot(time_slot: TimeSlot, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                time_slot.is_active = False
                time_slot.save()
            else:
                time_slot.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def reorder_time_slots(academic_year_id: int, slot_ids_in_order: List[int]) -> bool:
        try:
            with transaction.atomic():
                for idx, slot_id in enumerate(slot_ids_in_order, start=1):
                    TimeSlot.objects.filter(id=slot_id, academic_year_id=academic_year_id).update(order=idx)
            return True
        except Exception:
            return False