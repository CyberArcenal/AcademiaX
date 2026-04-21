from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import date, time

from ..models.student_attendance import StudentAttendance
from ...students.models.student import Student
from ...classes.models.section import Section
from ...academic.models.subject import Subject
from ...classes.models.academic_year import AcademicYear
from ...teachers.models.teacher import Teacher
from ...common.enums.attendance import AttendanceStatus, LateReason

class StudentAttendanceService:
    """Service for StudentAttendance model operations"""

    @staticmethod
    def create_attendance(
        student: Student,
        section: Section,
        subject: Subject,
        academic_year: AcademicYear,
        date: date,
        status: str = AttendanceStatus.PRESENT,
        time_in: Optional[time] = None,
        time_out: Optional[time] = None,
        late_minutes: int = 0,
        late_reason: Optional[str] = None,
        remarks: str = "",
        marked_by: Optional[Teacher] = None
    ) -> StudentAttendance:
        try:
            with transaction.atomic():
                attendance = StudentAttendance(
                    student=student,
                    section=section,
                    subject=subject,
                    academic_year=academic_year,
                    date=date,
                    status=status,
                    time_in=time_in,
                    time_out=time_out,
                    late_minutes=late_minutes,
                    late_reason=late_reason,
                    remarks=remarks,
                    marked_by=marked_by
                )
                attendance.full_clean()
                attendance.save()
                return attendance
        except ValidationError as e:
            raise

    @staticmethod
    def get_attendance_by_id(attendance_id: int) -> Optional[StudentAttendance]:
        try:
            return StudentAttendance.objects.get(id=attendance_id)
        except StudentAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendance_by_student_date(
        student_id: int,
        date: date,
        subject_id: int,
        section_id: int
    ) -> Optional[StudentAttendance]:
        try:
            return StudentAttendance.objects.get(
                student_id=student_id,
                date=date,
                subject_id=subject_id,
                section_id=section_id
            )
        except StudentAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendance_by_student_academic_year(
        student_id: int,
        academic_year_id: int
    ) -> List[StudentAttendance]:
        return StudentAttendance.objects.filter(
            student_id=student_id,
            academic_year_id=academic_year_id
        ).order_by('-date')

    @staticmethod
    def get_attendance_by_section_date(
        section_id: int,
        date: date
    ) -> List[StudentAttendance]:
        return StudentAttendance.objects.filter(
            section_id=section_id,
            date=date
        ).select_related('student', 'subject')

    @staticmethod
    def update_attendance(attendance: StudentAttendance, update_data: Dict[str, Any]) -> StudentAttendance:
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
    def delete_attendance(attendance: StudentAttendance) -> bool:
        try:
            attendance.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def bulk_create_attendance(attendance_list: List[Dict]) -> List[StudentAttendance]:
        created = []
        with transaction.atomic():
            for data in attendance_list:
                attendance = StudentAttendance(**data)
                attendance.full_clean()
                attendance.save()
                created.append(attendance)
        return created

    @staticmethod
    def mark_absent_for_date(
        section_id: int,
        subject_id: int,
        academic_year_id: int,
        date: date,
        student_ids: List[int]
    ) -> int:
        """Bulk mark multiple students as absent for a specific date"""
        attendance_objects = []
        for student_id in student_ids:
            attendance_objects.append(
                StudentAttendance(
                    student_id=student_id,
                    section_id=section_id,
                    subject_id=subject_id,
                    academic_year_id=academic_year_id,
                    date=date,
                    status=AttendanceStatus.ABSENT
                )
            )
        with transaction.atomic():
            created_count = StudentAttendance.objects.bulk_create(attendance_objects)
            return len(created_count)

    @staticmethod
    def get_attendance_rate(
        student_id: int,
        academic_year_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> float:
        """Calculate attendance percentage for a student over a period"""
        queryset = StudentAttendance.objects.filter(
            student_id=student_id,
            academic_year_id=academic_year_id
        )
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        total_days = queryset.count()
        if total_days == 0:
            return 0.0

        present_days = queryset.filter(status=AttendanceStatus.PRESENT).count()
        return (present_days / total_days) * 100