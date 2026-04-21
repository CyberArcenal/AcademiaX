from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.fee_structure import FeeStructure
from ...classes.models.academic_year import AcademicYear
from ...classes.models.grade_level import GradeLevel
from ...academic.models.academic_program import AcademicProgram
from ...common.enums.fees import FeeCategory

class FeeStructureService:
    """Service for FeeStructure model operations"""

    @staticmethod
    def create_fee_structure(
        name: str,
        category: str,
        amount: Decimal,
        academic_year: AcademicYear,
        grade_level: Optional[GradeLevel] = None,
        academic_program: Optional[AcademicProgram] = None,
        is_mandatory: bool = True,
        is_per_semester: bool = True,
        due_date: Optional[date] = None,
        description: str = ""
    ) -> FeeStructure:
        try:
            with transaction.atomic():
                fee_structure = FeeStructure(
                    name=name,
                    category=category,
                    amount=amount,
                    academic_year=academic_year,
                    grade_level=grade_level,
                    academic_program=academic_program,
                    is_mandatory=is_mandatory,
                    is_per_semester=is_per_semester,
                    due_date=due_date,
                    description=description
                )
                fee_structure.full_clean()
                fee_structure.save()
                return fee_structure
        except ValidationError as e:
            raise

    @staticmethod
    def get_fee_structure_by_id(fee_id: int) -> Optional[FeeStructure]:
        try:
            return FeeStructure.objects.get(id=fee_id)
        except FeeStructure.DoesNotExist:
            return None

    @staticmethod
    def get_fee_structures_by_academic_year(academic_year_id: int) -> List[FeeStructure]:
        return FeeStructure.objects.filter(academic_year_id=academic_year_id).select_related('grade_level', 'academic_program')

    @staticmethod
    def get_fee_structures_for_student(grade_level_id: int, academic_program_id: Optional[int] = None, academic_year_id: int = None) -> List[FeeStructure]:
        """Get applicable fee structures for a student based on grade level and program"""
        queryset = FeeStructure.objects.filter(
            academic_year_id=academic_year_id,
            is_active=True
        )
        # Filter by grade level (if specific)
        queryset = queryset.filter(grade_level_id=grade_level_id)
        # Filter by academic program (if provided)
        if academic_program_id:
            queryset = queryset.filter(academic_program_id=academic_program_id)
        return queryset

    @staticmethod
    def update_fee_structure(fee_structure: FeeStructure, update_data: Dict[str, Any]) -> FeeStructure:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(fee_structure, field):
                        setattr(fee_structure, field, value)
                fee_structure.full_clean()
                fee_structure.save()
                return fee_structure
        except ValidationError as e:
            raise

    @staticmethod
    def delete_fee_structure(fee_structure: FeeStructure, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                fee_structure.is_active = False
                fee_structure.save()
            else:
                fee_structure.delete()
            return True
        except Exception:
            return False