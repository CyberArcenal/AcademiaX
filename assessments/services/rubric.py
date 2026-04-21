from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.rubric import RubricCriterion, RubricLevel
from ..models.assessment import Assessment

class RubricCriterionService:
    """Service for RubricCriterion model operations"""

    @staticmethod
    def create_criterion(
        assessment: Assessment,
        name: str,
        max_points: Decimal,
        order: int = 0,
        description: str = ""
    ) -> RubricCriterion:
        try:
            with transaction.atomic():
                criterion = RubricCriterion(
                    assessment=assessment,
                    name=name,
                    description=description,
                    max_points=max_points,
                    order=order
                )
                criterion.full_clean()
                criterion.save()
                return criterion
        except ValidationError as e:
            raise

    @staticmethod
    def get_criterion_by_id(criterion_id: int) -> Optional[RubricCriterion]:
        try:
            return RubricCriterion.objects.get(id=criterion_id)
        except RubricCriterion.DoesNotExist:
            return None

    @staticmethod
    def get_criteria_by_assessment(assessment_id: int) -> List[RubricCriterion]:
        return RubricCriterion.objects.filter(assessment_id=assessment_id).order_by('order')

    @staticmethod
    def update_criterion(criterion: RubricCriterion, update_data: Dict[str, Any]) -> RubricCriterion:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(criterion, field):
                        setattr(criterion, field, value)
                criterion.full_clean()
                criterion.save()
                return criterion
        except ValidationError as e:
            raise

    @staticmethod
    def delete_criterion(criterion: RubricCriterion) -> bool:
        try:
            criterion.delete()
            return True
        except Exception:
            return False


class RubricLevelService:
    """Service for RubricLevel model operations"""

    @staticmethod
    def create_level(
        criterion: RubricCriterion,
        level_name: str,
        points: Decimal,
        description: str = ""
    ) -> RubricLevel:
        try:
            with transaction.atomic():
                level = RubricLevel(
                    criterion=criterion,
                    level_name=level_name,
                    description=description,
                    points=points
                )
                level.full_clean()
                level.save()
                return level
        except ValidationError as e:
            raise

    @staticmethod
    def get_level_by_id(level_id: int) -> Optional[RubricLevel]:
        try:
            return RubricLevel.objects.get(id=level_id)
        except RubricLevel.DoesNotExist:
            return None

    @staticmethod
    def get_levels_by_criterion(criterion_id: int) -> List[RubricLevel]:
        return RubricLevel.objects.filter(criterion_id=criterion_id).order_by('-points')

    @staticmethod
    def update_level(level: RubricLevel, update_data: Dict[str, Any]) -> RubricLevel:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(level, field):
                        setattr(level, field, value)
                level.full_clean()
                level.save()
                return level
        except ValidationError as e:
            raise

    @staticmethod
    def delete_level(level: RubricLevel) -> bool:
        try:
            level.delete()
            return True
        except Exception:
            return False