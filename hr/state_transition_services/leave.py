import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class LeaveRequestStateTransitionService:
    """Handles side effects of leave request state changes."""

    @staticmethod
    def handle_creation(leave):
        """When a new leave request is created, notify approver."""
        from communication.services.notification import NotificationService

        # Notify the employee's supervisor or HR
        supervisor = leave.employee.supervisor
        if supervisor and supervisor.user:
            NotificationService.create_notification(
                recipient=supervisor.user,
                title="Leave Request Pending",
                message=f"{leave.employee.user.get_full_name()} requested {leave.get_leave_type_display()} from {leave.start_date} to {leave.end_date}.",
                notification_type='INFO'
            )
            logger.info(f"Leave request {leave.id} created, supervisor notified")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            LeaveRequestStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(leave, old_status, new_status):
        """Handle leave request approval/rejection."""
        from communication.services.notification import NotificationService

        if new_status == 'APP' and old_status != 'APP':
            # Approved: update employee status to ON_LEAVE if the leave period covers today
            today = timezone.now().date()
            if leave.start_date <= today <= leave.end_date:
                leave.employee.status = 'LV'
                leave.employee.save()
                logger.info(f"Employee {leave.employee.id} status set to ON_LEAVE due to approved leave")
            # Notify employee
            if leave.employee.user:
                NotificationService.create_notification(
                    recipient=leave.employee.user,
                    title="Leave Request Approved",
                    message=f"Your {leave.get_leave_type_display()} request from {leave.start_date} to {leave.end_date} has been approved.",
                    notification_type='INFO'
                )
            logger.info(f"Leave request {leave.id} approved")

        elif new_status == 'REJ' and old_status != 'REJ':
            # Rejected: notify employee
            if leave.employee.user:
                NotificationService.create_notification(
                    recipient=leave.employee.user,
                    title="Leave Request Rejected",
                    message=f"Your {leave.get_leave_type_display()} request has been rejected. Reason: {leave.remarks}",
                    notification_type='ALERT'
                )
            logger.info(f"Leave request {leave.id} rejected")