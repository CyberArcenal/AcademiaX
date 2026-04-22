from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date, time

from attendance.models.teacher_attendance import TeacherAttendance
from common.enums.attendance import AttendanceStatus
from teachers.models.teacher import Teacher
from users.models.user import User



class TeacherAttendanceService:
    """Service for TeacherAttendance model operations"""

    @staticmethod
    def create_attendance(
        teacher: Teacher,
        date: date,
        status: str = AttendanceStatus.PRESENT,
        time_in: Optional[time] = None,
        time_out: Optional[time] = None,
        late_minutes: int = 0,
        remarks: str = "",
        recorded_by: Optional[User] = None
    ) -> TeacherAttendance:
        try:
            with transaction.atomic():
                attendance = TeacherAttendance(
                    teacher=teacher,
                    date=date,
                    status=status,
                    time_in=time_in,
                    time_out=time_out,
                    late_minutes=late_minutes,
                    remarks=remarks,
                    recorded_by=recorded_by
                )
                attendance.full_clean()
                attendance.save()
                return attendance
        except ValidationError as e:
            raise

    @staticmethod
    def get_attendance_by_id(attendance_id: int) -> Optional[TeacherAttendance]:
        try:
            return TeacherAttendance.objects.get(id=attendance_id)
        except TeacherAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendance_by_teacher_date(teacher_id: int, date: date) -> Optional[TeacherAttendance]:
        try:
            return TeacherAttendance.objects.get(teacher_id=teacher_id, date=date)
        except TeacherAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendance_by_teacher(teacher_id: int, limit: int = 30) -> List[TeacherAttendance]:
        return TeacherAttendance.objects.filter(teacher_id=teacher_id).order_by('-date')[:limit]

    @staticmethod
    def get_attendance_by_date(date: date) -> List[TeacherAttendance]:
        return TeacherAttendance.objects.filter(date=date).select_related('teacher')

    @staticmethod
    def update_attendance(attendance: TeacherAttendance, update_data: Dict[str, Any]) -> TeacherAttendance:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(attendance, field):
                        setattr(attendance, field, value)
                attendance.full_clean()
                attendance.save()
                return attendance
        except ValidationError as e:
            raise

    @staticmethod
    def delete_attendance(attendance: TeacherAttendance) -> bool:
        try:
            attendance.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_attendance_rate(teacher_id: int, start_date: date, end_date: date) -> float:
        """Calculate attendance percentage for a teacher over a period"""
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            return 0.0

        present_days = TeacherAttendance.objects.filter(
            teacher_id=teacher_id,
            date__gte=start_date,
            date__lte=end_date,
            status=AttendanceStatus.PRESENT
        ).count()
        return (present_days / total_days) * 100