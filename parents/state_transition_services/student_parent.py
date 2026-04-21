import logging

from parents.models.student_parent import StudentParent

logger = logging.getLogger(__name__)


class StudentParentStateTransitionService:
    """Handles side effects of student-parent relationship changes."""

    @staticmethod
    def handle_creation(relationship):
        """When a new relationship is created, ensure at most one primary per student."""
        if relationship.is_primary_contact:
            # Unset other primary contacts for the same student
            StudentParent.objects.filter(
                student=relationship.student,
                is_primary_contact=True
            ).exclude(id=relationship.id).update(is_primary_contact=False)
            logger.info(f"Set {relationship.id} as primary contact for student {relationship.student.id}")

    @staticmethod
    def handle_deletion(relationship):
        """When a relationship is deleted, if it was primary, assign another primary."""
        if relationship.is_primary_contact:
            # Find another relationship for the same student
            other = StudentParent.objects.filter(student=relationship.student).exclude(id=relationship.id).first()
            if other:
                other.is_primary_contact = True
                other.save()
                logger.info(f"Promoted relationship {other.id} to primary after deletion of {relationship.id}")