from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List

from ..models.prerequisite import Prerequisite
from ..models.subject import Subject

class PrerequisiteService:
    """Service for Prerequisite model operations"""

    @staticmethod
    def add_prerequisite(
        subject: Subject,
        required_subject: Subject,
        is_optional: bool = False,
        notes: str = ""
    ) -> Prerequisite:
        try:
            with transaction.atomic():
                prereq = Prerequisite(
                    subject=subject,
                    required_subject=required_subject,
                    is_optional=is_optional,
                    notes=notes
                )
                prereq.full_clean()
                prereq.save()
                return prereq
        except ValidationError as e:
            raise

    @staticmethod
    def get_prerequisites_for_subject(subject_id: int) -> List[Prerequisite]:
        return Prerequisite.objects.filter(subject_id=subject_id).select_related('required_subject')

    @staticmethod
    def get_subjects_requiring(subject_id: int) -> List[Prerequisite]:
        return Prerequisite.objects.filter(required_subject_id=subject_id).select_related('subject')

    @staticmethod
    def remove_prerequisite(prereq: Prerequisite) -> bool:
        try:
            prereq.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def update_prerequisite(prereq: Prerequisite, is_optional: bool, notes: str) -> Prerequisite:
        prereq.is_optional = is_optional
        prereq.notes = notes
        prereq.save()
        return prereq

    @staticmethod
    def check_prerequisites(subject: Subject, completed_subject_ids: List[int]) -> bool:
        """Check if a student has completed all required prerequisites for a subject"""
        required = Prerequisite.objects.filter(subject=subject, is_optional=False)
        required_ids = list(required.values_list('required_subject_id', flat=True))
        return all(req_id in completed_subject_ids for req_id in required_ids)