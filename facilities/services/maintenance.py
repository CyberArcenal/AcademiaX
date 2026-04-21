from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.maintenance import MaintenanceRequest
from ..models.facility import Facility
from ..models.equipment import Equipment
from ...users.models import User
from ...common.enums.facilities import MaintenancePriority, MaintenanceStatus

class MaintenanceRequestService:
    """Service for MaintenanceRequest model operations"""

    @staticmethod
    def create_request(
        reported_by: User,
        title: str,
        description: str,
        facility: Optional[Facility] = None,
        equipment: Optional[Equipment] = None,
        priority: str = MaintenancePriority.MEDIUM,
        assigned_to: Optional[User] = None,
        scheduled_date: Optional[date] = None
    ) -> MaintenanceRequest:
        try:
            with transaction.atomic():
                if not facility and not equipment:
                    raise ValidationError("Either facility or equipment must be specified")

                request = MaintenanceRequest(
                    facility=facility,
                    equipment=equipment,
                    reported_by=reported_by,
                    title=title,
                    description=description,
                    priority=priority,
                    status=MaintenanceStatus.PENDING,
                    assigned_to=assigned_to,
                    scheduled_date=scheduled_date
                )
                request.full_clean()
                request.save()
                return request
        except ValidationError as e:
            raise

    @staticmethod
    def get_request_by_id(request_id: int) -> Optional[MaintenanceRequest]:
        try:
            return MaintenanceRequest.objects.get(id=request_id)
        except MaintenanceRequest.DoesNotExist:
            return None

    @staticmethod
    def get_requests_by_facility(facility_id: int) -> List[MaintenanceRequest]:
        return MaintenanceRequest.objects.filter(facility_id=facility_id).order_by('-created_at')

    @staticmethod
    def get_requests_by_equipment(equipment_id: int) -> List[MaintenanceRequest]:
        return MaintenanceRequest.objects.filter(equipment_id=equipment_id).order_by('-created_at')

    @staticmethod
    def get_pending_requests() -> List[MaintenanceRequest]:
        return MaintenanceRequest.objects.filter(status=MaintenanceStatus.PENDING).order_by('-priority', '-created_at')

    @staticmethod
    def update_request(request: MaintenanceRequest, update_data: Dict[str, Any]) -> MaintenanceRequest:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(request, field):
                        setattr(request, field, value)
                request.full_clean()
                request.save()
                return request
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(
        request: MaintenanceRequest,
        status: str,
        assigned_to: Optional[User] = None,
        completed_date: Optional[date] = None,
        cost: Optional[float] = None,
        remarks: str = ""
    ) -> MaintenanceRequest:
        request.status = status
        if assigned_to:
            request.assigned_to = assigned_to
        if status == MaintenanceStatus.COMPLETED:
            request.completed_date = completed_date or date.today()
        if cost is not None:
            request.cost = cost
        if remarks:
            request.remarks = remarks
        request.save()
        return request

    @staticmethod
    def delete_request(request: MaintenanceRequest) -> bool:
        try:
            request.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_requests_by_status(status: str) -> List[MaintenanceRequest]:
        return MaintenanceRequest.objects.filter(status=status)