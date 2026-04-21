from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.facility import Facility
from ..models.building import Building
from ...common.enums.facilities import FacilityType, FacilityStatus

class FacilityService:
    """Service for Facility model operations"""

    @staticmethod
    def create_facility(
        building: Building,
        name: str,
        facility_type: str,
        room_number: str = "",
        floor: Optional[int] = None,
        capacity: int = 0,
        description: str = "",
        features: List[str] = None,
        status: str = FacilityStatus.AVAILABLE,
        is_active: bool = True
    ) -> Facility:
        try:
            with transaction.atomic():
                facility = Facility(
                    building=building,
                    name=name,
                    facility_type=facility_type,
                    room_number=room_number,
                    floor=floor,
                    capacity=capacity,
                    status=status,
                    description=description,
                    features=features or [],
                    is_active=is_active
                )
                facility.full_clean()
                facility.save()
                return facility
        except ValidationError as e:
            raise

    @staticmethod
    def get_facility_by_id(facility_id: int) -> Optional[Facility]:
        try:
            return Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            return None

    @staticmethod
    def get_facilities_by_building(building_id: int, active_only: bool = True) -> List[Facility]:
        queryset = Facility.objects.filter(building_id=building_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def get_facilities_by_type(facility_type: str, active_only: bool = True) -> List[Facility]:
        queryset = Facility.objects.filter(facility_type=facility_type)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def update_facility(facility: Facility, update_data: Dict[str, Any]) -> Facility:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(facility, field):
                        setattr(facility, field, value)
                facility.full_clean()
                facility.save()
                return facility
        except ValidationError as e:
            raise

    @staticmethod
    def delete_facility(facility: Facility, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                facility.is_active = False
                facility.save()
            else:
                facility.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def update_status(facility: Facility, status: str) -> Facility:
        facility.status = status
        facility.save()
        return facility

    @staticmethod
    def get_available_facilities(facility_type: Optional[str] = None) -> List[Facility]:
        queryset = Facility.objects.filter(status=FacilityStatus.AVAILABLE, is_active=True)
        if facility_type:
            queryset = queryset.filter(facility_type=facility_type)
        return queryset