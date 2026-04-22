from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.test_schedule import Schedule
from ..models.test_time_slot import TimeSlot
from ...classes.models.section import Section
from ...academic.models.subject import Subject
from ...teachers.models.teacher import Teacher
from ...facilities.models.facility import Facility
from ...classes.models.term import Term
from ...common.enums.timetable import ScheduleType

class ScheduleService:
    """Service for Schedule model operations"""

    @staticmethod
    def create_schedule(
        time_slot: TimeSlot,
        section: Section,
        subject: Subject,
        teacher: Teacher,
        room: Facility,
        term: Term,
        schedule_type: str = ScheduleType.REGULAR,
        is_active: bool = True,
        notes: str = ""
    ) -> Schedule:
        try:
            with transaction.atomic():
                # Check for conflicts
                # 1. Same section cannot have two classes at same time slot
                if Schedule.objects.filter(time_slot=time_slot, section=section, term=term).exists():
                    raise ValidationError(f"Section {section.name} already has a class at this time slot")

                # 2. Teacher cannot be double-booked
                if Schedule.objects.filter(time_slot=time_slot, teacher=teacher, term=term).exists():
                    raise ValidationError(f"Teacher {teacher.get_full_name()} already has a class at this time slot")

                # 3. Room cannot be double-booked
                if Schedule.objects.filter(time_slot=time_slot, room=room, term=term).exists():
                    raise ValidationError(f"Room {room.name} is already occupied at this time slot")

                schedule = Schedule(
                    time_slot=time_slot,
                    section=section,
                    subject=subject,
                    teacher=teacher,
                    room=room,
                    term=term,
                    schedule_type=schedule_type,
                    is_active=is_active,
                    notes=notes
                )
                schedule.full_clean()
                schedule.save()
                return schedule
        except ValidationError as e:
            raise

    @staticmethod
    def get_schedule_by_id(schedule_id: int) -> Optional[Schedule]:
        try:
            return Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return None

    @staticmethod
    def get_schedules_by_section(section_id: int, term_id: Optional[int] = None) -> List[Schedule]:
        queryset = Schedule.objects.filter(section_id=section_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        return queryset.select_related('time_slot', 'subject', 'teacher', 'room')

    @staticmethod
    def get_schedules_by_teacher(teacher_id: int, term_id: Optional[int] = None) -> List[Schedule]:
        queryset = Schedule.objects.filter(teacher_id=teacher_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        return queryset.select_related('time_slot', 'section', 'subject')

    @staticmethod
    def get_schedules_by_room(room_id: int, term_id: Optional[int] = None) -> List[Schedule]:
        queryset = Schedule.objects.filter(room_id=room_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        return queryset.order_by('time_slot__day_of_week', 'time_slot__order')

    @staticmethod
    def update_schedule(schedule: Schedule, update_data: Dict[str, Any]) -> Schedule:
        try:
            with transaction.atomic():
                # Check for conflicts if time_slot, teacher, room, or section changes
                new_time_slot = update_data.get('time_slot', schedule.time_slot)
                new_section = update_data.get('section', schedule.section)
                new_teacher = update_data.get('teacher', schedule.teacher)
                new_room = update_data.get('room', schedule.room)
                term = update_data.get('term', schedule.term)

                if 'time_slot' in update_data or 'section' in update_data:
                    if Schedule.objects.filter(time_slot=new_time_slot, section=new_section, term=term).exclude(id=schedule.id).exists():
                        raise ValidationError("Section already has a class at this time slot")
                if 'time_slot' in update_data or 'teacher' in update_data:
                    if Schedule.objects.filter(time_slot=new_time_slot, teacher=new_teacher, term=term).exclude(id=schedule.id).exists():
                        raise ValidationError("Teacher already has a class at this time slot")
                if 'time_slot' in update_data or 'room' in update_data:
                    if Schedule.objects.filter(time_slot=new_time_slot, room=new_room, term=term).exclude(id=schedule.id).exists():
                        raise ValidationError("Room is already occupied at this time slot")

                for field, value in update_data.items():
                    if hasattr(schedule, field):
                        setattr(schedule, field, value)
                schedule.full_clean()
                schedule.save()
                return schedule
        except ValidationError as e:
            raise

    @staticmethod
    def delete_schedule(schedule: Schedule, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                schedule.is_active = False
                schedule.save()
            else:
                schedule.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_class_schedule_for_student(student_id: int, term_id: int) -> List[Schedule]:
        from ...enrollments.models import Enrollment
        enrollment = Enrollment.objects.filter(student_id=student_id, status='ENR').first()
        if enrollment:
            return Schedule.objects.filter(section=enrollment.section, term_id=term_id, is_active=True)
        return []