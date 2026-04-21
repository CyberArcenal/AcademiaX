import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class PayslipStateTransitionService:
    """Handles side effects of payslip creation/update."""

    @staticmethod
    def handle_creation(payslip):
        """When a new payslip is generated, notify employee."""
        from communication.services.notification import NotificationService

        if payslip.employee.user:
            NotificationService.create_notification(
                recipient=payslip.employee.user,
                title="New Payslip Available",
                message=f"A new payslip for period {payslip.period.name} is available. Net pay: {payslip.net_pay}",
                notification_type='INFO',
                action_url=f"/hr/payslips/{payslip.id}/"
            )
            logger.info(f"Payslip {payslip.id} generated, notification sent to employee {payslip.employee.id}")

    @staticmethod
    def handle_update(payslip):
        """When payslip is updated (e.g., payment date set), send notification."""
        from communication.services.notification import NotificationService

        # If payment_date was just set and not previously set
        if payslip.payment_date and not hasattr(payslip, '_payment_notified'):
            if payslip.employee.user:
                NotificationService.create_notification(
                    recipient=payslip.employee.user,
                    title="Salary Paid",
                    message=f"Your salary for period {payslip.period.name} has been paid on {payslip.payment_date}.",
                    notification_type='PAYMENT'
                )
                payslip._payment_notified = True
                logger.info(f"Payment notification sent for payslip {payslip.id}")