from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.classroom import Classroom
from ...common.enums.classes import RoomType

class ClassroomService:
    """Service for Classroom model operations"""

    @staticmethod
    def create_classroom(
        room_number: str,
        building: str = "",
        floor: Optional[int] = None,
        capacity: int = 30,
        room_type: str = RoomType.CLASSROOM,
        has_projector: bool = False,
        has_aircon: bool = False,
        is_active: bool = True
    ) -> Classroom:
        try:
            with transaction.atomic():
                classroom = Classroom(
                    room_number=room_number,
                    building=building,
                    floor=floor,
                    capacity=capacity,
                    room_type=room_type,
                    has_projector=has_projector,
                    has_aircon=has_aircon,
                    is_active=is_active
                )
                classroom.full_clean()
                classroom.save()
                return classroom
        except ValidationError as e:
            raise

    @staticmethod
    def get_classroom_by_id(classroom_id: int) -> Optional[Classroom]:
        try:
            return Classroom.objects.get(id=classroom_id)
        except Classroom.DoesNotExist:
            return None

    @staticmethod
    def get_classroom_by_number(room_number: str) -> Optional[Classroom]:
        try:
            return Classroom.objects.get(room_number=room_number)
        except Classroom.DoesNotExist:
            return None

    @staticmethod
    def get_all_classrooms(active_only: bool = True) -> List[Classroom]:
        queryset = Classroom.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def get_classrooms_by_building(building: str, active_only: bool = True) -> List[Classroom]:
        queryset = Classroom.objects.filter(building__iexact=building)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def update_classroom(classroom: Classroom, update_data: Dict[str, Any]) -> Classroom:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(classroom, field):
                        setattr(classroom, field, value)
                classroom.full_clean()
                classroom.save()
                return classroom
        except ValidationError as e:
            raise

    @staticmethod
    def delete_classroom(classroom: Classroom, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                classroom.is_active = False
                classroom.save()
            else:
                classroom.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_available_classrooms(time_slot_id: Optional[int] = None, date: Optional[date] = None) -> List[Classroom]:
        """Get classrooms that are not reserved at a given time (simplified)"""
        from ...timetable.models import Schedule, RoomSchedule
        queryset = Classroom.objects.filter(is_active=True)
        if time_slot_id and date:
            # Exclude classrooms with schedule on that time slot and date
            booked = Schedule.objects.filter(time_slot_id=time_slot_id).values_list('room_id', flat=True)
            booked_rooms = set(booked)
            # Also check room schedules (events)
            room_events = RoomSchedule.objects.filter(time_slot_id=time_slot_id, date=date).values_list('room_id', flat=True)
            booked_rooms.update(room_events)
            queryset = queryset.exclude(id__in=booked_rooms)
        return queryset