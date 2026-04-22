from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List
from decimal import Decimal

from attendance.models.attendance_summary import StudentAttendanceSummary
from classes.models.academic_year import AcademicYear
from common.enums.attendance import AttendanceStatus
from students.models.student import Student



class StudentAttendanceSummaryService:
    """Service for StudentAttendanceSummary model operations"""

    @staticmethod
    def create_or_update_summary(
        student: Student,
        academic_year: AcademicYear,
        term: str,
        total_present: int = 0,
        total_absent: int = 0,
        total_late: int = 0,
        total_excused: int = 0,
        attendance_rate: Decimal = Decimal('0')
    ) -> StudentAttendanceSummary:
        try:
            with transaction.atomic():
                summary, created = StudentAttendanceSummary.objects.update_or_create(
                    student=student,
                    academic_year=academic_year,
                    term=term,
                    defaults={
                        'total_present': total_present,
                        'total_absent': total_absent,
                        'total_late': total_late,
                        'total_excused': total_excused,
                        'attendance_rate': attendance_rate
                    }
                )
                summary.full_clean()
                summary.save()
                return summary
        except ValidationError as e:
            raise

    @staticmethod
    def get_summary_by_id(summary_id: int) -> Optional[StudentAttendanceSummary]:
        try:
            return StudentAttendanceSummary.objects.get(id=summary_id)
        except StudentAttendanceSummary.DoesNotExist:
            return None

    @staticmethod
    def get_summary_by_student_term(
        student_id: int,
        academic_year_id: int,
        term: str
    ) -> Optional[StudentAttendanceSummary]:
        try:
            return StudentAttendanceSummary.objects.get(
                student_id=student_id,
                academic_year_id=academic_year_id,
                term=term
            )
        except StudentAttendanceSummary.DoesNotExist:
            return None

    @staticmethod
    def get_summaries_by_student(student_id: int) -> List[StudentAttendanceSummary]:
        return StudentAttendanceSummary.objects.filter(student_id=student_id).order_by('academic_year__start_date')

    @staticmethod
    def update_summary_from_attendance(
        student_id: int,
        academic_year_id: int,
        term: str,
        start_date: date,
        end_date: date
    ) -> StudentAttendanceSummary:
        """Recalculate summary based on raw attendance records"""
        from ..models.student_attendance import StudentAttendance

        attendances = StudentAttendance.objects.filter(
            student_id=student_id,
            academic_year_id=academic_year_id,
            date__gte=start_date,
            date__lte=end_date
        )

        total_present = attendances.filter(status=AttendanceStatus.PRESENT).count()
        total_absent = attendances.filter(status=AttendanceStatus.ABSENT).count()
        total_late = attendances.filter(status=AttendanceStatus.LATE).count()
        total_excused = attendances.filter(status=AttendanceStatus.EXCUSED).count()

        total_days = attendances.count()
        attendance_rate = Decimal('0')
        if total_days > 0:
            attendance_rate = Decimal((total_present / total_days) * 100).quantize(Decimal('0.01'))

        return StudentAttendanceSummaryService.create_or_update_summary(
            student=Student.objects.get(id=student_id),
            academic_year=AcademicYear.objects.get(id=academic_year_id),
            term=term,
            total_present=total_present,
            total_absent=total_absent,
            total_late=total_late,
            total_excused=total_excused,
            attendance_rate=attendance_rate
        )

    @staticmethod
    def delete_summary(summary: StudentAttendanceSummary) -> bool:
        try:
            summary.delete()
            return True
        except Exception:
            return False