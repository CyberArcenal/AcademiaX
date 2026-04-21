from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.leave import LeaveRequest
from ..models.employee import Employee
from ...common.enums.hr import LeaveType, LeaveStatus

class LeaveRequestService:
    """Service for LeaveRequest model operations"""

    @staticmethod
    def create_leave_request(
        employee: Employee,
        leave_type: str,
        start_date: date,
        end_date: date,
        reason: str,
        remarks: str = ""
    ) -> LeaveRequest:
        try:
            with transaction.atomic():
                days_requested = (end_date - start_date).days + 1
                if days_requested <= 0:
                    raise ValidationError("End date must be after start date")

                leave = LeaveRequest(
                    employee=employee,
                    leave_type=leave_type,
                    start_date=start_date,
                    end_date=end_date,
                    days_requested=days_requested,
                    reason=reason,
                    status=LeaveStatus.PENDING,
                    remarks=remarks
                )
                leave.full_clean()
                leave.save()
                return leave
        except ValidationError as e:
            raise

    @staticmethod
    def get_leave_by_id(leave_id: int) -> Optional[LeaveRequest]:
        try:
            return LeaveRequest.objects.get(id=leave_id)
        except LeaveRequest.DoesNotExist:
            return None

    @staticmethod
    def get_leaves_by_employee(employee_id: int, year: Optional[int] = None) -> List[LeaveRequest]:
        queryset = LeaveRequest.objects.filter(employee_id=employee_id)
        if year:
            queryset = queryset.filter(start_date__year=year)
        return queryset.order_by('-start_date')

    @staticmethod
    def get_pending_leaves() -> List[LeaveRequest]:
        return LeaveRequest.objects.filter(status=LeaveStatus.PENDING).order_by('start_date')

    @staticmethod
    def update_leave_status(
        leave: LeaveRequest,
        status: str,
        approved_by: Optional[Employee] = None,
        remarks: str = ""
    ) -> LeaveRequest:
        leave.status = status
        if approved_by:
            leave.approved_by = approved_by
            leave.approved_at = timezone.now()
        if remarks:
            leave.remarks = remarks
        leave.save()
        return leave

    @staticmethod
    def delete_leave(leave: LeaveRequest) -> bool:
        try:
            leave.delete()
            return True
        except Exception:
            return False