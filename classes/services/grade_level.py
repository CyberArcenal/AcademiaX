from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from classes.models.grade_level import GradeLevel


class GradeLevelService:
    """Service for GradeLevel model operations"""

    @staticmethod
    def create_grade_level(
        level: str,
        name: str,
        order: int
    ) -> GradeLevel:
        try:
            with transaction.atomic():
                grade_level = GradeLevel(
                    level=level,
                    name=name,
                    order=order
                )
                grade_level.full_clean()
                grade_level.save()
                return grade_level
        except ValidationError as e:
            raise

    @staticmethod
    def get_grade_level_by_id(grade_level_id: int) -> Optional[GradeLevel]:
        try:
            return GradeLevel.objects.get(id=grade_level_id)
        except GradeLevel.DoesNotExist:
            return None

    @staticmethod
    def get_grade_level_by_level(level: str) -> Optional[GradeLevel]:
        try:
            return GradeLevel.objects.get(level=level)
        except GradeLevel.DoesNotExist:
            return None

    @staticmethod
    def get_all_grade_levels() -> List[GradeLevel]:
        return GradeLevel.objects.all().order_by('order')

    @staticmethod
    def update_grade_level(grade_level: GradeLevel, update_data: Dict[str, Any]) -> GradeLevel:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(grade_level, field):
                        setattr(grade_level, field, value)
                grade_level.full_clean()
                grade_level.save()
                return grade_level
        except ValidationError as e:
            raise

    @staticmethod
    def delete_grade_level(grade_level: GradeLevel, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                grade_level.is_active = False
                grade_level.save()
            else:
                grade_level.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def reorder_grade_levels(level_ids_in_order: List[int]) -> bool:
        try:
            with transaction.atomic():
                for idx, level_id in enumerate(level_ids_in_order, start=1):
                    GradeLevel.objects.filter(id=level_id).update(order=idx)
            return True
        except Exception:
            return False