from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.event import AlumniEvent, EventAttendance
from ..models.alumni import Alumni
from ...common.enums.alumni import RSVPStatus

class AlumniEventService:
    """Service for AlumniEvent model operations"""

    @staticmethod
    def create_event(
        title: str,
        event_date: datetime,
        location: str,
        registration_deadline: datetime,
        description: str = "",
        max_attendees: Optional[int] = None,
        is_online: bool = False,
        meeting_link: str = ""
    ) -> AlumniEvent:
        try:
            with transaction.atomic():
                event = AlumniEvent(
                    title=title,
                    description=description,
                    event_date=event_date,
                    location=location,
                    max_attendees=max_attendees,
                    is_online=is_online,
                    meeting_link=meeting_link,
                    registration_deadline=registration_deadline
                )
                event.full_clean()
                event.save()
                return event
        except ValidationError as e:
            raise

    @staticmethod
    def get_event_by_id(event_id: int) -> Optional[AlumniEvent]:
        try:
            return AlumniEvent.objects.get(id=event_id)
        except AlumniEvent.DoesNotExist:
            return None

    @staticmethod
    def get_upcoming_events(limit: int = 10) -> List[AlumniEvent]:
        return AlumniEvent.objects.filter(event_date__gte=timezone.now()).order_by('event_date')[:limit]

    @staticmethod
    def get_past_events(limit: int = 10) -> List[AlumniEvent]:
        return AlumniEvent.objects.filter(event_date__lt=timezone.now()).order_by('-event_date')[:limit]

    @staticmethod
    def update_event(event: AlumniEvent, update_data: Dict[str, Any]) -> AlumniEvent:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(event, field):
                        setattr(event, field, value)
                event.full_clean()
                event.save()
                return event
        except ValidationError as e:
            raise

    @staticmethod
    def delete_event(event: AlumniEvent) -> bool:
        try:
            event.delete()
            return True
        except Exception:
            return False


class EventAttendanceService:
    """Service for EventAttendance model operations"""

    @staticmethod
    def create_attendance(
        alumni: Alumni,
        event: AlumniEvent,
        rsvp_status: str = RSVPStatus.NO_RESPONSE,
        attended: bool = False,
        notes: str = ""
    ) -> EventAttendance:
        try:
            with transaction.atomic():
                attendance = EventAttendance(
                    alumni=alumni,
                    event=event,
                    rsvp_status=rsvp_status,
                    attended=attended,
                    notes=notes
                )
                attendance.full_clean()
                attendance.save()
                return attendance
        except ValidationError as e:
            raise

    @staticmethod
    def get_attendance_by_id(attendance_id: int) -> Optional[EventAttendance]:
        try:
            return EventAttendance.objects.get(id=attendance_id)
        except EventAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendances_by_event(event_id: int) -> List[EventAttendance]:
        return EventAttendance.objects.filter(event_id=event_id).select_related('alumni')

    @staticmethod
    def get_attendances_by_alumni(alumni_id: int) -> List[EventAttendance]:
        return EventAttendance.objects.filter(alumni_id=alumni_id).select_related('event')

    @staticmethod
    def update_rsvp(attendance: EventAttendance, rsvp_status: str) -> EventAttendance:
        attendance.rsvp_status = rsvp_status
        attendance.save()
        return attendance

    @staticmethod
    def mark_attended(attendance: EventAttendance, checked_in_at: Optional[datetime] = None) -> EventAttendance:
        attendance.attended = True
        attendance.checked_in_at = checked_in_at or timezone.now()
        attendance.save()
        return attendance

    @staticmethod
    def delete_attendance(attendance: EventAttendance) -> bool:
        try:
            attendance.delete()
            return True
        except Exception:
            return False