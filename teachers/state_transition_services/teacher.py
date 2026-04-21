import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class TeacherStateTransitionService:
    """Handles side effects of teacher state changes."""

    @staticmethod
    def handle_creation(teacher):
        """When a new teacher is created, ensure user role is TEACHER."""
        if teacher.user and teacher.user.role != 'TEACHER':
            teacher.user.role = 'TEACHER'
            teacher.user.save()
            logger.info(f"Updated user {teacher.user.id} role to TEACHER")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            TeacherStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )
        if 'is_active' in changes:
            TeacherStateTransitionService._handle_is_active_change(
                instance, changes['is_active']['old'], changes['is_active']['new']
            )
        if 'user' in changes:
            TeacherStateTransitionService._handle_user_change(
                instance, changes['user']['old'], changes['user']['new']
            )

    @staticmethod
    def _handle_status_change(teacher, old_status, new_status):
        """Handle teacher status transitions."""
        # When teacher resigns or is terminated, deactivate teaching assignments
        if new_status in ['RES', 'TER'] and old_status not in ['RES', 'TER']:
            from teachers.services.teaching_assignment import TeachingAssignmentService
            assignments = teacher.assignments.filter(is_active=True)
            for assignment in assignments:
                TeachingAssignmentService.update_assignment(assignment, {'is_active': False})
            logger.info(f"Deactivated {assignments.count()} teaching assignments for teacher {teacher.id}")

        # When teacher returns from leave (status becomes ACTIVE again), reactivate assignments? Optional.
        if new_status == 'ACT' and old_status == 'LV':
            # Optionally reactivate assignments, but careful with overlapping terms.
            # For simplicity, we'll not auto-reactivate; admin should handle.
            logger.info(f"Teacher {teacher.id} returned from leave, assignments may need manual reactivation")

    @staticmethod
    def _handle_is_active_change(teacher, old_value, new_value):
        """Handle teacher activation/deactivation (soft delete)."""
        if new_value is False and old_value is True:
            if teacher.user:
                teacher.user.is_active = False
                teacher.user.save()
            # Also deactivate teaching assignments
            from teachers.services.teaching_assignment import TeachingAssignmentService
            assignments = teacher.assignments.filter(is_active=True)
            for assignment in assignments:
                TeachingAssignmentService.update_assignment(assignment, {'is_active': False})
            logger.info(f"Deactivated teacher {teacher.id} and linked user, and deactivated {assignments.count()} assignments")
        elif new_value is True and old_value is False:
            if teacher.user:
                teacher.user.is_active = True
                teacher.user.save()
            logger.info(f"Reactivated teacher {teacher.id} and linked user")

    @staticmethod
    def _handle_user_change(teacher, old_user_id, new_user_id):
        """When a user is linked or unlinked."""
        if new_user_id and not old_user_id:
            if teacher.user and teacher.user.role != 'TEACHER':
                teacher.user.role = 'TEACHER'
                teacher.user.save()
                logger.info(f"Linked user {new_user_id} to teacher {teacher.id} and set role TEACHER")
        elif old_user_id and not new_user_id:
            logger.warning(f"Teacher {teacher.id} unlinked from user {old_user_id}")