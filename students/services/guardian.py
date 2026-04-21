from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.guardian import Guardian
from ..models.student import Student
from ...common.enums.parents import RelationshipType

class GuardianService:
    """Service for Guardian model operations"""

    @staticmethod
    def create_guardian(
        student: Student,
        first_name: str,
        last_name: str,
        relationship: str,
        contact_number: str,
        middle_name: str = "",
        email: str = "",
        occupation: str = "",
        is_primary: bool = False,
        lives_with_student: bool = True
    ) -> Guardian:
        try:
            with transaction.atomic():
                if is_primary:
                    Guardian.objects.filter(student=student, is_primary=True).update(is_primary=False)

                guardian = Guardian(
                    student=student,
                    first_name=first_name.title(),
                    last_name=last_name.title(),
                    middle_name=middle_name.title(),
                    relationship=relationship,
                    contact_number=contact_number,
                    email=email,
                    occupation=occupation,
                    is_primary=is_primary,
                    lives_with_student=lives_with_student
                )
                guardian.full_clean()
                guardian.save()
                return guardian
        except ValidationError as e:
            raise

    @staticmethod
    def get_guardian_by_id(guardian_id: int) -> Optional[Guardian]:
        try:
            return Guardian.objects.get(id=guardian_id)
        except Guardian.DoesNotExist:
            return None

    @staticmethod
    def get_guardians_by_student(student_id: int) -> List[Guardian]:
        return Guardian.objects.filter(student_id=student_id).order_by('-is_primary')

    @staticmethod
    def get_primary_guardian(student_id: int) -> Optional[Guardian]:
        try:
            return Guardian.objects.get(student_id=student_id, is_primary=True)
        except Guardian.DoesNotExist:
            return None

    @staticmethod
    def update_guardian(guardian: Guardian, update_data: Dict[str, Any]) -> Guardian:
        try:
            with transaction.atomic():
                if update_data.get('is_primary') and not guardian.is_primary:
                    Guardian.objects.filter(student=guardian.student, is_primary=True).update(is_primary=False)

                for field, value in update_data.items():
                    if hasattr(guardian, field):
                        if field in ['first_name', 'last_name', 'middle_name']:
                            value = value.title()
                        setattr(guardian, field, value)
                guardian.full_clean()
                guardian.save()
                return guardian
        except ValidationError as e:
            raise

    @staticmethod
    def delete_guardian(guardian: Guardian) -> bool:
        try:
            guardian.delete()
            return True
        except Exception:
            return False