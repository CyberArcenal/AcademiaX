from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date, time

from ..models.attendance import EmployeeAttendance
from ..models.employee import Employee
from ...common.enums.hr import AttendanceStatus

class EmployeeAttendanceService:
    """Service for EmployeeAttendance model operations"""

    @staticmethod
    def create_attendance(
        employee: Employee,
        date: date,
        status: str = AttendanceStatus.PRESENT,
        time_in: Optional[time] = None,
        time_out: Optional[time] = None,
        late_minutes: int = 0,
        undertime_minutes: int = 0,
        remarks: str = "",
        recorded_by: Optional[Employee] = None
    ) -> EmployeeAttendance:
        try:
            with transaction.atomic():
                # Check if attendance already exists for this employee and date
                existing = EmployeeAttendance.objects.filter(employee=employee, date=date).first()
                if existing:
                    raise ValidationError("Attendance already recorded for this date")

                attendance = EmployeeAttendance(
                    employee=employee,
                    date=date,
                    status=status,
                    time_in=time_in,
                    time_out=time_out,
                    late_minutes=late_minutes,
                    undertime_minutes=undertime_minutes,
                    remarks=remarks,
                    recorded_by=recorded_by
                )
                attendance.full_clean()
                attendance.save()
                return attendance
        except ValidationError as e:
            raise

    @staticmethod
    def get_attendance_by_id(attendance_id: int) -> Optional[EmployeeAttendance]:
        try:
            return EmployeeAttendance.objects.get(id=attendance_id)
        except EmployeeAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendance_by_employee_date(employee_id: int, date: date) -> Optional[EmployeeAttendance]:
        try:
            return EmployeeAttendance.objects.get(employee_id=employee_id, date=date)
        except EmployeeAttendance.DoesNotExist:
            return None

    @staticmethod
    def get_attendance_by_employee(employee_id: int, month: Optional[int] = None, year: Optional[int] = None) -> List[EmployeeAttendance]:
        queryset = EmployeeAttendance.objects.filter(employee_id=employee_id)
        if year:
            queryset = queryset.filter(date__year=year)
        if month:
            queryset = queryset.filter(date__month=month)
        return queryset.order_by('-date')

    @staticmethod
    def update_attendance(attendance: EmployeeAttendance, update_data: Dict[str, Any]) -> EmployeeAttendance:
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
    def delete_attendance(attendance: EmployeeAttendance) -> bool:
        try:
            attendance.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_attendance_rate(employee_id: int, start_date: date, end_date: date) -> float:
        total_days = (end_date - start_date).days + 1
        present_days = EmployeeAttendance.objects.filter(
            employee_id=employee_id,
            date__gte=start_date,
            date__lte=end_date,
            status=AttendanceStatus.PRESENT
        ).count()
        return (present_days / total_days) * 100 if total_days > 0 else 0