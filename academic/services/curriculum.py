from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.curriculum import Curriculum
from ..models.academic_program import AcademicProgram

class CurriculumService:
    """Service for Curriculum model operations"""

    @staticmethod
    def create_curriculum(
        academic_program: AcademicProgram,
        grade_level: str,
        year_effective: int,
        is_current: bool = False
    ) -> Curriculum:
        try:
            with transaction.atomic():
                # If setting is_current=True, unset previous current for same program & grade
                if is_current:
                    Curriculum.objects.filter(
                        academic_program=academic_program,
                        grade_level=grade_level
                    ).update(is_current=False)

                curriculum = Curriculum(
                    academic_program=academic_program,
                    grade_level=grade_level,
                    year_effective=year_effective,
                    is_current=is_current
                )
                curriculum.full_clean()
                curriculum.save()
                return curriculum
        except ValidationError as e:
            raise

    @staticmethod
    def get_curriculum_by_id(curriculum_id: int) -> Optional[Curriculum]:
        try:
            return Curriculum.objects.get(id=curriculum_id)
        except Curriculum.DoesNotExist:
            return None

    @staticmethod
    def get_current_curriculum(academic_program_id: int, grade_level: str) -> Optional[Curriculum]:
        try:
            return Curriculum.objects.get(
                academic_program_id=academic_program_id,
                grade_level=grade_level,
                is_current=True
            )
        except Curriculum.DoesNotExist:
            return None

    @staticmethod
    def get_curricula_by_program(program_id: int) -> List[Curriculum]:
        return Curriculum.objects.filter(academic_program_id=program_id).order_by('-year_effective')

    @staticmethod
    def update_curriculum(curriculum: Curriculum, update_data: Dict[str, Any]) -> Curriculum:
        try:
            with transaction.atomic():
                if update_data.get('is_current') and not curriculum.is_current:
                    # Unset others
                    Curriculum.objects.filter(
                        academic_program=curriculum.academic_program,
                        grade_level=curriculum.grade_level
                    ).update(is_current=False)

                for field, value in update_data.items():
                    if hasattr(curriculum, field):
                        setattr(curriculum, field, value)
                curriculum.full_clean()
                curriculum.save()
                return curriculum
        except ValidationError as e:
            raise

    @staticmethod
    def delete_curriculum(curriculum: Curriculum, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                curriculum.is_active = False
                curriculum.save()
            else:
                curriculum.delete()
            return True
        except Exception:
            return False