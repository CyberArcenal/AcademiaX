import logging

logger = logging.getLogger(__name__)


class ParentStateTransitionService:
    """Handles side effects of parent state changes."""

    @staticmethod
    def handle_creation(parent):
        """When a new parent record is created, ensure user role is PARENT."""
        if parent.user and parent.user.role != 'PARENT':
            parent.user.role = 'PARENT'
            parent.user.save()
            logger.info(f"Updated user {parent.user.id} role to PARENT")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            ParentStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(parent, old_status, new_status):
        """Handle parent status transitions."""
        from communication.services.notification import NotificationService

        if new_status == 'BLK' and old_status != 'BLK':
            # Blacklisted: notify all linked students? Optional.
            for sp in parent.students.all():
                student = sp.student
                if student.user:
                    NotificationService.create_notification(
                        recipient=student.user,
                        title="Parent Account Restricted",
                        message=f"Your parent/guardian account has been restricted. Please contact the school.",
                        notification_type='ALERT'
                    )
            logger.info(f"Parent {parent.id} blacklisted, notifications sent to linked students")
        elif new_status == 'ACT' and old_status == 'BLK':
            # Reactivated
            logger.info(f"Parent {parent.id} reactivated from blacklist")