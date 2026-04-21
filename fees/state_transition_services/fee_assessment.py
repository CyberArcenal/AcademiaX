import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class FeeAssessmentStateTransitionService:
    """Handles side effects of fee assessment state changes."""

    @staticmethod
    def handle_creation(assessment):
        """When a new fee assessment is created, optionally send notification."""
        from communication.services.notification import NotificationService
        enrollment = assessment.enrollment
        student = enrollment.student
        if student.user:
            NotificationService.create_notification(
                recipient=student.user,
                title="New Fee Assessment",
                message=f"A new fee of {assessment.amount} is due on {assessment.due_date}.",
                notification_type='PAYMENT'
            )
        logger.info(f"Created fee assessment {assessment.id} for enrollment {enrollment.id}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            FeeAssessmentStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(assessment, old_status, new_status):
        """When assessment status changes, possibly update enrollment payment status."""
        enrollment = assessment.enrollment
        if new_status == 'PD' and old_status != 'PD':
            # Check if all assessments for this enrollment are paid
            all_assessments = enrollment.fee_assessments.all()
            all_paid = all(a.status == 'PD' for a in all_assessments)
            if all_paid:
                enrollment.payment_status = 'PD'
                enrollment.save()
                logger.info(f"Enrollment {enrollment.id} marked fully paid")
            else:
                enrollment.payment_status = 'PRT'
                enrollment.save()
        elif new_status == 'OVD' and old_status != 'OVD':
            # Send overdue notification
            from communication.services.notification import NotificationService
            if enrollment.student.user:
                NotificationService.create_notification(
                    recipient=enrollment.student.user,
                    title="Payment Overdue",
                    message=f"Your payment of {assessment.amount} is overdue. Please settle immediately.",
                    notification_type='ALERT'
                )
            logger.info(f"Assessment {assessment.id} marked overdue, notification sent")