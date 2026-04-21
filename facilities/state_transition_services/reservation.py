import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class FacilityReservationStateTransitionService:
    """Handles side effects of facility reservation state changes."""

    @staticmethod
    def handle_creation(reservation):
        """When a new reservation is created, notify admin for approval."""
        from communication.services.notification import NotificationService

        # Notify facility manager or admin (simplified: get users with role 'ADMIN')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(role='ADMIN', is_active=True)
        for admin in admins:
            NotificationService.create_notification(
                recipient=admin,
                title="New Facility Reservation",
                message=f"{reservation.reserved_by.get_full_name()} requested to reserve {reservation.facility.name} on {reservation.start_datetime.date()}.",
                notification_type='INFO',
                action_url=f"/admin/facilities/reservations/{reservation.id}/"
            )
        logger.info(f"Reservation {reservation.id} created, admins notified")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            FacilityReservationStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(reservation, old_status, new_status):
        """Handle reservation status transitions."""
        from communication.services.notification import NotificationService

        # When approved
        if new_status == 'APP' and old_status != 'APP':
            # Update facility status to RESERVED for the duration? Optional.
            # Notify the person who made the reservation
            if reservation.reserved_by:
                NotificationService.create_notification(
                    recipient=reservation.reserved_by,
                    title="Reservation Approved",
                    message=f"Your reservation for {reservation.facility.name} on {reservation.start_datetime.date()} has been approved.",
                    notification_type='INFO'
                )
            logger.info(f"Reservation {reservation.id} approved")

        # When rejected
        if new_status == 'REJ' and old_status != 'REJ':
            if reservation.reserved_by:
                NotificationService.create_notification(
                    recipient=reservation.reserved_by,
                    title="Reservation Rejected",
                    message=f"Your reservation for {reservation.facility.name} has been rejected. Reason: {reservation.cancellation_reason}",
                    notification_type='ALERT'
                )
            logger.info(f"Reservation {reservation.id} rejected")

        # When cancelled
        if new_status == 'CNC' and old_status != 'CNC':
            if reservation.reserved_by and old_status == 'APP':
                NotificationService.create_notification(
                    recipient=reservation.reserved_by,
                    title="Reservation Cancelled",
                    message=f"Your approved reservation for {reservation.facility.name} has been cancelled. Reason: {reservation.cancellation_reason}",
                    notification_type='ALERT'
                )
            logger.info(f"Reservation {reservation.id} cancelled")

        # When completed (after the event)
        if new_status == 'CMP' and old_status != 'CMP':
            logger.info(f"Reservation {reservation.id} marked as completed")