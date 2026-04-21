import logging
from django.db import models
logger = logging.getLogger(__name__)


class DonationStateTransitionService:
    """Handles side effects of donation creation."""

    @staticmethod
    def handle_creation(donation):
        """When a donation is recorded, send thank you notification and update totals."""
        from communication.services.notification import NotificationService

        # Send thank you notification to alumni (if user exists)
        if donation.alumni.user:
            NotificationService.create_notification(
                recipient=donation.alumni.user,
                title="Thank You for Your Donation",
                message=f"Thank you for your donation of {donation.amount}. Your support means a lot!",
                notification_type='INFO'
            )
            logger.info(f"Thank you notification sent to alumni {donation.alumni.id} for donation {donation.id}")

        # Optionally update total donation amount for the alumni
        total = donation.alumni.donations.aggregate(total=models.Sum('amount'))['total']
        # Could store in a cached field on Alumni model if added
        logger.info(f"Donation {donation.id} recorded. New total for alumni {donation.alumni.id}: {total}")