from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.building import Building

class BuildingService:
    """Service for Building model operations"""

    @staticmethod
    def create_building(
        name: str,
        code: str,
        address: str = "",
        number_of_floors: int = 1,
        year_built: Optional[int] = None,
        is_active: bool = True
    ) -> Building:
        try:
            with transaction.atomic():
                building = Building(
                    name=name,
                    code=code.upper(),
                    address=address,
                    number_of_floors=number_of_floors,
                    year_built=year_built,
                    is_active=is_active
                )
                building.full_clean()
                building.save()
                return building
        except ValidationError as e:
            raise

    @staticmethod
    def get_building_by_id(building_id: int) -> Optional[Building]:
        try:
            return Building.objects.get(id=building_id)
        except Building.DoesNotExist:
            return None

    @staticmethod
    def get_building_by_code(code: str) -> Optional[Building]:
        try:
            return Building.objects.get(code=code.upper())
        except Building.DoesNotExist:
            return None

    @staticmethod
    def get_all_buildings(active_only: bool = True) -> List[Building]:
        queryset = Building.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('name')

    @staticmethod
    def update_building(building: Building, update_data: Dict[str, Any]) -> Building:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(building, field):
                        if field == 'code':
                            value = value.upper()
                        setattr(building, field, value)
                building.full_clean()
                building.save()
                return building
        except ValidationError as e:
            raise

    @staticmethod
    def delete_building(building: Building, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                building.is_active = False
                building.save()
            else:
                building.delete()
            return True
        except Exception:
            return False