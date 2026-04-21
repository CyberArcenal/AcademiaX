from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.room_schedule import RoomSchedule
from ..models.time_slot import TimeSlot
from ...facilities.models.facility import Facility

class RoomScheduleService:
    """Service for RoomSchedule model operations"""

    @staticmethod
    def create_room_schedule(
        room: Facility,
        time_slot: TimeSlot,
        event_name: str,
        date: date,
        description: str = "",
        is_recurring: bool = False,
        recurring_end_date: Optional[date] = None
    ) -> RoomSchedule:
        try:
            with transaction.atomic():
                # Check if room already has a schedule at this time slot and date
                if not is_recurring:
                    if RoomSchedule.objects.filter(room=room, time_slot=time_slot, date=date).exists():
                        raise ValidationError("Room already has a schedule at this time slot and date")

                room_schedule = RoomSchedule(
                    room=room,
                    time_slot=time_slot,
                    event_name=event_name,
                    description=description,
                    date=date,
                    is_recurring=is_recurring,
                    recurring_end_date=recurring_end_date if is_recurring else None
                )
                room_schedule.full_clean()
                room_schedule.save()
                return room_schedule
        except ValidationError as e:
            raise

    @staticmethod
    def get_room_schedule_by_id(room_schedule_id: int) -> Optional[RoomSchedule]:
        try:
            return RoomSchedule.objects.get(id=room_schedule_id)
        except RoomSchedule.DoesNotExist:
            return None

    @staticmethod
    def get_schedules_by_room(room_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[RoomSchedule]:
        queryset = RoomSchedule.objects.filter(room_id=room_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset.order_by('date', 'time_slot__order')

    @staticmethod
    def get_schedules_by_time_slot(time_slot_id: int, date: Optional[date] = None) -> List[RoomSchedule]:
        queryset = RoomSchedule.objects.filter(time_slot_id=time_slot_id)
        if date:
            queryset = queryset.filter(date=date)
        return queryset

    @staticmethod
    def update_room_schedule(room_schedule: RoomSchedule, update_data: Dict[str, Any]) -> RoomSchedule:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(room_schedule, field):
                        setattr(room_schedule, field, value)
                room_schedule.full_clean()
                room_schedule.save()
                return room_schedule
        except ValidationError as e:
            raise

    @staticmethod
    def delete_room_schedule(room_schedule: RoomSchedule) -> bool:
        try:
            room_schedule.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_room_availability(room_id: int, date: date) -> List[Dict]:
        """Get time slots where room is free on a given date"""
        all_time_slots = TimeSlot.objects.filter(is_active=True)
        booked_time_slot_ids = RoomSchedule.objects.filter(room_id=room_id, date=date).values_list('time_slot_id', flat=True)
        available = all_time_slots.exclude(id__in=booked_time_slot_ids)
        return [{'id': ts.id, 'name': ts.name, 'start_time': ts.start_time, 'end_time': ts.end_time} for ts in available]