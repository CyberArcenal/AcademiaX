import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class StudentStateTransitionService:
    """Handles side effects of student state changes."""

    @staticmethod
    def handle_creation(student):
        """Actions when a new student is created."""
        # Create an empty medical record
        from students.services.medical_record import MedicalRecordService
        MedicalRecordService.create_or_update_record(student=student)
        logger.info(f"Created default medical record for student {student.id}")

        # If user is linked, ensure role is STUDENT
        if student.user and student.user.role != 'STUDENT':
            student.user.role = 'STUDENT'
            student.user.save()
            logger.info(f"Updated user {student.user.id} role to STUDENT")

    @staticmethod
    def handle_changes(instance, changes):
        """Dispatch to specific handlers."""
        if 'status' in changes:
            StudentStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )
        if 'is_active' in changes:
            StudentStateTransitionService._handle_is_active_change(
                instance, changes['is_active']['old'], changes['is_active']['new']
            )
        if 'user' in changes:
            StudentStateTransitionService._handle_user_change(
                instance, changes['user']['old'], changes['user']['new']
            )

    @staticmethod
    def _handle_status_change(student, old_status, new_status):
        """Handle student status transitions."""
        # When student graduates, create alumni record
        if new_status == 'GRD' and old_status != 'GRD':
            from alumni.services.alumni import AlumniService
            AlumniService.create_alumni(
                student=student,
                graduation_year=timezone.now().year,
                user=student.user
            )
            logger.info(f"Created alumni record for student {student.id} upon graduation")

        # When student transfers or drops, update active enrollments
        if new_status in ['TRF', 'DRP'] and old_status not in ['TRF', 'DRP']:
            from enrollments.services.enrollment import EnrollmentService
            enrollments = student.enrollments.filter(status='ENR')
            for enrollment in enrollments:
                EnrollmentService.update_status(enrollment, new_status)
            logger.info(f"Updated {enrollments.count()} enrollments for student {student.id} to {new_status}")

        # When student goes on leave, freeze enrollments? (optional)
        if new_status == 'LV' and old_status != 'LV':
            from enrollments.services.enrollment import EnrollmentService
            enrollments = student.enrollments.filter(status='ENR')
            for enrollment in enrollments:
                EnrollmentService.update_status(enrollment, 'LV')
            logger.info(f"Put {enrollments.count()} enrollments on leave for student {student.id}")

    @staticmethod
    def _handle_is_active_change(student, old_value, new_value):
        """Handle student activation/deactivation (soft delete)."""
        if new_value is False and old_value is True:
            # Deactivation: also deactivate linked user if any
            if student.user:
                student.user.is_active = False
                student.user.save()
            # Optionally: cancel any pending enrollments? Not needed.
            logger.info(f"Deactivated student {student.id} and linked user")
        elif new_value is True and old_value is False:
            # Reactivation
            if student.user:
                student.user.is_active = True
                student.user.save()
            logger.info(f"Reactivated student {student.id} and linked user")

    @staticmethod
    def _handle_user_change(student, old_user_id, new_user_id):
        """When a user is linked or unlinked."""
        if new_user_id and not old_user_id:
            # User linked: update role
            if student.user and student.user.role != 'STUDENT':
                student.user.role = 'STUDENT'
                student.user.save()
                logger.info(f"Linked user {new_user_id} to student {student.id} and set role STUDENT")
        elif old_user_id and not new_user_id:
            # User unlinked: do nothing, but maybe log
            logger.warning(f"Student {student.id} unlinked from user {old_user_id}")