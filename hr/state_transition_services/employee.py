import logging

logger = logging.getLogger(__name__)


class EmployeeStateTransitionService:
    """Handles side effects of employee state changes."""

    @staticmethod
    def handle_creation(employee):
        """When a new employee is created, ensure user role is appropriate."""
        if employee.user:
            # Determine role based on position/department (simplified)
            if employee.position and 'teacher' in employee.position.title.lower():
                expected_role = 'TEACHER'
            else:
                expected_role = 'STAFF'
            if employee.user.role != expected_role:
                employee.user.role = expected_role
                employee.user.save()
            logger.info(f"Employee {employee.id} created, user {employee.user.id} role set to {expected_role}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            EmployeeStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )
        if 'is_active' in changes:
            EmployeeStateTransitionService._handle_is_active_change(
                instance, changes['is_active']['old'], changes['is_active']['new']
            )

    @staticmethod
    def _handle_status_change(employee, old_status, new_status):
        """Handle employee status transitions."""
        from communication.services.notification import NotificationService

        # When employee resigns or is terminated, deactivate user account
        if new_status in ['RES', 'TER'] and old_status not in ['RES', 'TER']:
            if employee.user:
                employee.user.is_active = False
                employee.user.save()
                logger.info(f"User {employee.user.id} deactivated due to employee {employee.id} status {new_status}")

        # When employee goes on leave
        if new_status == 'LV' and old_status != 'LV':
            # Notify supervisor? Optional.
            logger.info(f"Employee {employee.id} went on leave")

        # When employee returns from leave
        if new_status == 'ACT' and old_status == 'LV':
            logger.info(f"Employee {employee.id} returned from leave")

        # Send notification to employee
        if employee.user:
            NotificationService.create_notification(
                recipient=employee.user,
                title="Employment Status Updated",
                message=f"Your employment status has been changed to {new_status}.",
                notification_type='INFO'
            )
            logger.info(f"Notification sent to employee {employee.id} about status change")

    @staticmethod
    def _handle_is_active_change(employee, old_value, new_value):
        """Handle employee activation/deactivation (soft delete)."""
        if new_value is False and old_value is True:
            if employee.user:
                employee.user.is_active = False
                employee.user.save()
            logger.info(f"Employee {employee.id} deactivated")
        elif new_value is True and old_value is False:
            if employee.user:
                employee.user.is_active = True
                employee.user.save()
            logger.info(f"Employee {employee.id} reactivated")