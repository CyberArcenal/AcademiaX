from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.student_parent import StudentParent
from ..models.parent import Parent
from students.models.student import Student
from common.enums.parents import RelationshipType

class StudentParentService:
    """Service for StudentParent model operations"""

    @staticmethod
    def create_relationship(
        student: Student,
        parent: Parent,
        relationship: str,
        is_primary_contact: bool = False,
        can_pickup: bool = True,
        receives_academic_updates: bool = True,
        receives_disciplinary_updates: bool = True,
        receives_payment_reminders: bool = True,
        notes: str = ""
    ) -> StudentParent:
        try:
            with transaction.atomic():
                # Check if relationship already exists
                existing = StudentParent.objects.filter(student=student, parent=parent).first()
                if existing:
                    raise ValidationError("Relationship already exists")

                # If setting is_primary_contact, unset others for this student
                if is_primary_contact:
                    StudentParent.objects.filter(student=student, is_primary_contact=True).update(is_primary_contact=False)

                relationship_obj = StudentParent(
                    student=student,
                    parent=parent,
                    relationship=relationship,
                    is_primary_contact=is_primary_contact,
                    can_pickup=can_pickup,
                    receives_academic_updates=receives_academic_updates,
                    receives_disciplinary_updates=receives_disciplinary_updates,
                    receives_payment_reminders=receives_payment_reminders,
                    notes=notes
                )
                relationship_obj.full_clean()
                relationship_obj.save()
                return relationship_obj
        except ValidationError as e:
            raise

    @staticmethod
    def get_relationship_by_id(rel_id: int) -> Optional[StudentParent]:
        try:
            return StudentParent.objects.get(id=rel_id)
        except StudentParent.DoesNotExist:
            return None

    @staticmethod
    def get_relationships_by_student(student_id: int) -> List[StudentParent]:
        return StudentParent.objects.filter(student_id=student_id).select_related('parent__user')

    @staticmethod
    def get_relationships_by_parent(parent_id: int) -> List[StudentParent]:
        return StudentParent.objects.filter(parent_id=parent_id).select_related('student')

    @staticmethod
    def get_primary_contact(student_id: int) -> Optional[StudentParent]:
        try:
            return StudentParent.objects.get(student_id=student_id, is_primary_contact=True)
        except StudentParent.DoesNotExist:
            return None

    @staticmethod
    def update_relationship(relationship: StudentParent, update_data: Dict[str, Any]) -> StudentParent:
        try:
            with transaction.atomic():
                # Handle primary contact change
                if update_data.get('is_primary_contact') and not relationship.is_primary_contact:
                    StudentParent.objects.filter(student=relationship.student, is_primary_contact=True).update(is_primary_contact=False)

                for field, value in update_data.items():
                    if hasattr(relationship, field):
                        setattr(relationship, field, value)
                relationship.full_clean()
                relationship.save()
                return relationship
        except ValidationError as e:
            raise

    @staticmethod
    def delete_relationship(relationship: StudentParent) -> bool:
        try:
            relationship.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_notification_preferences(parent_id: int, student_id: Optional[int] = None):
        """Get combined notification preferences for a parent across all or specific student"""
        queryset = StudentParent.objects.filter(parent_id=parent_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        return queryset