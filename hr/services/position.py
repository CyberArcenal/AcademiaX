from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.position import Position
from ..models.department import Department

class PositionService:
    """Service for Position model operations"""

    @staticmethod
    def create_position(
        title: str,
        department: Department,
        salary_grade: int = 1,
        is_active: bool = True
    ) -> Position:
        try:
            with transaction.atomic():
                position = Position(
                    title=title,
                    department=department,
                    salary_grade=salary_grade,
                    is_active=is_active
                )
                position.full_clean()
                position.save()
                return position
        except ValidationError as e:
            raise

    @staticmethod
    def get_position_by_id(position_id: int) -> Optional[Position]:
        try:
            return Position.objects.get(id=position_id)
        except Position.DoesNotExist:
            return None

    @staticmethod
    def get_positions_by_department(department_id: int, active_only: bool = True) -> List[Position]:
        queryset = Position.objects.filter(department_id=department_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def update_position(position: Position, update_data: Dict[str, Any]) -> Position:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(position, field):
                        setattr(position, field, value)
                position.full_clean()
                position.save()
                return position
        except ValidationError as e:
            raise

    @staticmethod
    def delete_position(position: Position, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                position.is_active = False
                position.save()
            else:
                position.delete()
            return True
        except Exception:
            return False