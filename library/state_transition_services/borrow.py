import logging
from django.utils import timezone
from datetime import date

logger = logging.getLogger(__name__)


class BorrowTransactionStateTransitionService:
    """Handles side effects of borrow transaction state changes."""

    @staticmethod
    def handle_creation(borrow):
        """When a new borrow transaction is created, update copy status."""
        from library.services.copy import BookCopyService
        BookCopyService.update_status(borrow.copy, 'BRW')
        logger.info(f"Borrow transaction {borrow.id} created, copy {borrow.copy.id} marked as BORROWED")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            BorrowTransactionStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(borrow, old_status, new_status):
        """When borrow status changes."""
        from library.services.copy import BookCopyService
        from library.services.fine import FineService

        # When returned
        if new_status == 'RTN' and old_status != 'RTN':
            BookCopyService.update_status(borrow.copy, 'AVL')
            # Check overdue
            if borrow.return_date and borrow.return_date > borrow.due_date:
                days_overdue = (borrow.return_date - borrow.due_date).days
                FineService.create_fine(borrow, days_overdue)
                logger.info(f"Fine created for overdue borrow {borrow.id}, {days_overdue} days")
            logger.info(f"Borrow transaction {borrow.id} returned, copy {borrow.copy.id} marked AVAILABLE")

        # When overdue (status changed to OVERDUE)
        if new_status == 'OVD' and old_status != 'OVD':
            # Send notification to borrower
            from communication.services.notification import NotificationService
            if borrow.borrower.user:
                NotificationService.create_notification(
                    recipient=borrow.borrower.user,
                    title="Book Overdue",
                    message=f"The book '{borrow.copy.book.title}' is overdue. Please return it immediately.",
                    notification_type='ALERT'
                )
            logger.info(f"Borrow transaction {borrow.id} marked overdue, notification sent")