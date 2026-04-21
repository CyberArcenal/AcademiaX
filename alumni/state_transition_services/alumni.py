import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class AlumniStateTransitionService:
    """Handles side effects of alumni state changes."""

    @staticmethod
    def handle_creation(alumni):
        """When a new alumni record is created, ensure user role is ALUMNI if user exists."""
        if alumni.user and alumni.user.role != 'ALUMNI':
            alumni.user.role = 'ALUMNI'
            alumni.user.save()
            logger.info(f"Updated user {alumni.user.id} role to ALUMNI")
        logger.info(f"Alumni record {alumni.id} created for student {alumni.student}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'is_active' in changes:
            AlumniStateTransitionService._handle_is_active_change(
                instance, changes['is_active']['old'], changes['is_active']['new']
            )

    @staticmethod
    def _handle_is_active_change(alumni, old_value, new_value):
        """Handle alumni activation/deactivation (soft delete)."""
        if new_value is False and old_value is True:
            # Deactivation: optionally deactivate linked user
            if alumni.user:
                alumni.user.is_active = False
                alumni.user.save()
            logger.info(f"Deactivated alumni {alumni.id} and linked user")
        elif new_value is True and old_value is False:
            # Reactivation
            if alumni.user:
                alumni.user.is_active = True
                alumni.user.save()
            logger.info(f"Reactivated alumni {alumni.id} and linked user")