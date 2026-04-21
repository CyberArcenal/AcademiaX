from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.curriculum import CurriculumSubject
from ..models.curriculum import Curriculum
from ..models.subject import Subject

class CurriculumSubjectService:
    """Service for CurriculumSubject model operations"""

    @staticmethod
    def add_subject_to_curriculum(
        curriculum: Curriculum,
        subject: Subject,
        year_level_order: int,
        semester: str = None,
        sequence: int = 0,
        is_required: bool = True
    ) -> CurriculumSubject:
        try:
            with transaction.atomic():
                cs = CurriculumSubject(
                    curriculum=curriculum,
                    subject=subject,
                    year_level_order=year_level_order,
                    semester=semester,
                    sequence=sequence,
                    is_required=is_required
                )
                cs.full_clean()
                cs.save()
                return cs
        except ValidationError as e:
            raise

    @staticmethod
    def get_curriculum_subject_by_id(cs_id: int) -> Optional[CurriculumSubject]:
        try:
            return CurriculumSubject.objects.get(id=cs_id)
        except CurriculumSubject.DoesNotExist:
            return None

    @staticmethod
    def get_subjects_by_curriculum(curriculum_id: int) -> List[CurriculumSubject]:
        return CurriculumSubject.objects.filter(curriculum_id=curriculum_id).select_related('subject')

    @staticmethod
    def update_curriculum_subject(cs: CurriculumSubject, update_data: Dict[str, Any]) -> CurriculumSubject:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(cs, field):
                        setattr(cs, field, value)
                cs.full_clean()
                cs.save()
                return cs
        except ValidationError as e:
            raise

    @staticmethod
    def remove_subject_from_curriculum(cs: CurriculumSubject) -> bool:
        try:
            cs.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def reorder_sequence(curriculum_id: int, subject_ids_in_order: List[int]) -> bool:
        """Bulk update sequence numbers"""
        try:
            with transaction.atomic():
                for idx, subject_id in enumerate(subject_ids_in_order, start=1):
                    CurriculumSubject.objects.filter(
                        curriculum_id=curriculum_id,
                        subject_id=subject_id
                    ).update(sequence=idx)
            return True
        except Exception:
            return False