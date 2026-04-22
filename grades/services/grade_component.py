from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.grade_component import GradeComponent
from academic.models.subject import Subject
from classes.models.academic_year import AcademicYear
from classes.models.grade_level import GradeLevel

class GradeComponentService:
    """Service for GradeComponent model operations"""

    @staticmethod
    def create_component(
        name: str,
        weight: Decimal,
        subject: Subject,
        academic_year: AcademicYear,
        grade_level: GradeLevel,
        is_active: bool = True
    ) -> GradeComponent:
        try:
            with transaction.atomic():
                component = GradeComponent(
                    name=name,
                    weight=weight,
                    subject=subject,
                    academic_year=academic_year,
                    grade_level=grade_level,
                    is_active=is_active
                )
                component.full_clean()
                component.save()
                return component
        except ValidationError as e:
            raise

    @staticmethod
    def get_component_by_id(component_id: int) -> Optional[GradeComponent]:
        try:
            return GradeComponent.objects.get(id=component_id)
        except GradeComponent.DoesNotExist:
            return None

    @staticmethod
    def get_components_by_subject(subject_id: int, academic_year_id: int, grade_level_id: int) -> List[GradeComponent]:
        return GradeComponent.objects.filter(
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            grade_level_id=grade_level_id,
            is_active=True
        ).order_by('id')

    @staticmethod
    def update_component(component: GradeComponent, update_data: Dict[str, Any]) -> GradeComponent:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(component, field):
                        setattr(component, field, value)
                component.full_clean()
                component.save()
                return component
        except ValidationError as e:
            raise

    @staticmethod
    def delete_component(component: GradeComponent, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                component.is_active = False
                component.save()
            else:
                component.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def validate_weights(subject_id: int, academic_year_id: int, grade_level_id: int) -> bool:
        components = GradeComponent.objects.filter(
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            grade_level_id=grade_level_id,
            is_active=True
        )
        total_weight = sum(c.weight for c in components)
        return abs(total_weight - 100) < 0.01  # Should sum to 100