from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.specialization import Specialization
from ..models.teacher import Teacher
from ...academic.models.subject import Subject

class SpecializationService:
    """Service for Specialization model operations"""

    @staticmethod
    def create_specialization(
        teacher: Teacher,
        subject: Subject,
        is_primary: bool = False,
        proficiency_level: str = 'INTERMEDIATE'
    ) -> Specialization:
        try:
            with transaction.atomic():
                # If setting is_primary, unset previous primary for this teacher
                if is_primary:
                    Specialization.objects.filter(teacher=teacher, is_primary=True).update(is_primary=False)

                specialization = Specialization(
                    teacher=teacher,
                    subject=subject,
                    is_primary=is_primary,
                    proficiency_level=proficiency_level
                )
                specialization.full_clean()
                specialization.save()
                return specialization
        except ValidationError as e:
            raise

    @staticmethod
    def get_specialization_by_id(spec_id: int) -> Optional[Specialization]:
        try:
            return Specialization.objects.get(id=spec_id)
        except Specialization.DoesNotExist:
            return None

    @staticmethod
    def get_specializations_by_teacher(teacher_id: int) -> List[Specialization]:
        return Specialization.objects.filter(teacher_id=teacher_id).select_related('subject')

    @staticmethod
    def get_primary_specialization(teacher_id: int) -> Optional[Specialization]:
        try:
            return Specialization.objects.get(teacher_id=teacher_id, is_primary=True)
        except Specialization.DoesNotExist:
            return None

    @staticmethod
    def update_specialization(specialization: Specialization, update_data: Dict[str, Any]) -> Specialization:
        try:
            with transaction.atomic():
                if update_data.get('is_primary') and not specialization.is_primary:
                    Specialization.objects.filter(teacher=specialization.teacher, is_primary=True).update(is_primary=False)

                for field, value in update_data.items():
                    if hasattr(specialization, field):
                        setattr(specialization, field, value)
                specialization.full_clean()
                specialization.save()
                return specialization
        except ValidationError as e:
            raise

    @staticmethod
    def delete_specialization(specialization: Specialization) -> bool:
        try:
            specialization.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_teachers_by_subject(subject_id: int) -> List[Teacher]:
        specializations = Specialization.objects.filter(subject_id=subject_id).select_related('teacher')
        return [s.teacher for s in specializations]