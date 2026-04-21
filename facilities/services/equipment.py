from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.equipment import Equipment
from ..models.facility import Facility

class EquipmentService:
    """Service for Equipment model operations"""

    @staticmethod
    def create_equipment(
        name: str,
        serial_number: str,
        facility: Optional[Facility] = None,
        model: str = "",
        manufacturer: str = "",
        purchase_date: Optional[date] = None,
        warranty_expiry: Optional[date] = None,
        status: str = 'OPERATIONAL',
        notes: str = ""
    ) -> Equipment:
        try:
            with transaction.atomic():
                equipment = Equipment(
                    facility=facility,
                    name=name,
                    model=model,
                    serial_number=serial_number,
                    manufacturer=manufacturer,
                    purchase_date=purchase_date,
                    warranty_expiry=warranty_expiry,
                    status=status,
                    notes=notes
                )
                equipment.full_clean()
                equipment.save()
                return equipment
        except ValidationError as e:
            raise

    @staticmethod
    def get_equipment_by_id(equipment_id: int) -> Optional[Equipment]:
        try:
            return Equipment.objects.get(id=equipment_id)
        except Equipment.DoesNotExist:
            return None

    @staticmethod
    def get_equipment_by_serial(serial_number: str) -> Optional[Equipment]:
        try:
            return Equipment.objects.get(serial_number=serial_number)
        except Equipment.DoesNotExist:
            return None

    @staticmethod
    def get_equipment_by_facility(facility_id: int) -> List[Equipment]:
        return Equipment.objects.filter(facility_id=facility_id)

    @staticmethod
    def update_equipment(equipment: Equipment, update_data: Dict[str, Any]) -> Equipment:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(equipment, field):
                        setattr(equipment, field, value)
                equipment.full_clean()
                equipment.save()
                return equipment
        except ValidationError as e:
            raise

    @staticmethod
    def delete_equipment(equipment: Equipment, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                equipment.is_active = False
                equipment.save()
            else:
                equipment.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def update_equipment_status(equipment: Equipment, status: str) -> Equipment:
        equipment.status = status
        equipment.save()
        return equipment

    @staticmethod
    def get_equipment_by_status(status: str) -> List[Equipment]:
        return Equipment.objects.filter(status=status)