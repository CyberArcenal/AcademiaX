import logging
from django.db import transaction

logger = logging.getLogger(__name__)


class PaymentStateTransitionService:
    """Handles side effects of payment creation/updates."""

    @staticmethod
    def handle_creation(payment):
        """When a new payment is recorded, update assessment balance and send receipt."""
        assessment = payment.assessment
        from fees.services.fee_assessment import FeeAssessmentService
        FeeAssessmentService.update_balance(assessment, payment.amount)

        # Send payment confirmation notification
        from communication.services.notification import NotificationService
        enrollment = assessment.enrollment
        student = enrollment.student
        if student.user:
            NotificationService.create_notification(
                recipient=student.user,
                title="Payment Received",
                message=f"Your payment of {payment.amount} has been received. Reference: {payment.reference_number}",
                notification_type='PAYMENT'
            )
        logger.info(f"Payment {payment.id} applied to assessment {assessment.id}")

    @staticmethod
    def handle_update(payment):
        """When payment is updated (e.g., verified), maybe send additional notification."""
        if payment.is_verified and not hasattr(payment, '_verified_notified'):
            from communication.services.notification import NotificationService
            enrollment = payment.assessment.enrollment
            student = enrollment.student
            if student.user:
                NotificationService.create_notification(
                    recipient=student.user,
                    title="Payment Verified",
                    message=f"Your payment of {payment.amount} has been verified.",
                    notification_type='INFO'
                )
            payment._verified_notified = True
            logger.info(f"Payment {payment.id} verified notification sent")