import logging

logger = logging.getLogger(__name__)


class GuardianStateTransitionService:
    """Handles side effects of guardian state changes."""

    @staticmethod
    def handle_creation(guardian):
        """When a new guardian is created, ensure at most one primary per student."""
        if guardian.is_primary:
            GuardianStateTransitionService._ensure_single_primary(guardian.student, guardian)

    @staticmethod
    def handle_changes(instance, changes):
        if 'is_primary' in changes:
            GuardianStateTransitionService._handle_primary_change(
                instance, changes['is_primary']['old'], changes['is_primary']['new']
            )

    @staticmethod
    def handle_deletion(guardian):
        """When a guardian is deleted, if it was primary, set another as primary."""
        if guardian.is_primary:
            # Find another guardian for the same student
            other_guardian = guardian.student.guardians.exclude(id=guardian.id).first()
            if other_guardian:
                other_guardian.is_primary = True
                other_guardian.save()
                logger.info(f"Guardian {other_guardian.id} became primary after deletion of {guardian.id}")

    @staticmethod
    def _ensure_single_primary(student, new_primary):
        """Ensure only one primary guardian per student."""
        Guardian.objects.filter(student=student, is_primary=True).exclude(id=new_primary.id).update(is_primary=False)

    @staticmethod
    def _handle_primary_change(guardian, old_value, new_value):
        """When a guardian becomes primary, unset others."""
        if new_value is True and old_value is False:
            Guardian.objects.filter(student=guardian.student, is_primary=True).exclude(id=guardian.id).update(is_primary=False)
            logger.info(f"Guardian {guardian.id} set as primary for student {guardian.student.id}")