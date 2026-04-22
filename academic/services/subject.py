from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import models
from typing import Optional, List, Dict, Any

from academic.models.subject import Subject
from common.enums.academic import SubjectType

class SubjectService:
    """Service for Subject model operations"""

    @staticmethod
    def create_subject(
        code: str,
        name: str,
        units: float = 3.0,
        subject_type: str = SubjectType.CORE,
        description: str = "",
        is_active: bool = True,
        **extra_fields
    ) -> Subject:
        """Create a new subject"""
        try:
            with transaction.atomic():
                subject = Subject(
                    code=code.upper(),
                    name=name.title(),
                    units=units,
                    subject_type=subject_type,
                    description=description,
                    is_active=is_active,
                    **extra_fields
                )
                subject.full_clean()
                subject.save()
                return subject
        except ValidationError as e:
            raise
        except Exception as e:
            raise ValidationError(str(e))

    @staticmethod
    def get_subject_by_id(subject_id: int) -> Optional[Subject]:
        try:
            return Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return None

    @staticmethod
    def get_subject_by_code(code: str) -> Optional[Subject]:
        try:
            return Subject.objects.get(code=code.upper())
        except Subject.DoesNotExist:
            return None

    @staticmethod
    def get_all_subjects(active_only: bool = True, limit: int = 100) -> List[Subject]:
        queryset = Subject.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset[:limit]

    @staticmethod
    def update_subject(subject: Subject, update_data: Dict[str, Any]) -> Subject:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(subject, field):
                        if field == 'code':
                            value = value.upper()
                        elif field == 'name':
                            value = value.title()
                        setattr(subject, field, value)
                subject.full_clean()
                subject.save()
                return subject
        except ValidationError as e:
            raise

    @staticmethod
    def delete_subject(subject: Subject, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                subject.is_active = False
                subject.save()
            else:
                subject.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_subjects(query: str, limit: int = 20) -> List[Subject]:
        return Subject.objects.filter(
            models.Q(code__icontains=query.upper()) |
            models.Q(name__icontains=query.title())
        )[:limit]

    @staticmethod
    def get_subjects_by_type(subject_type: str) -> List[Subject]:
        return Subject.objects.filter(subject_type=subject_type, is_active=True)