import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class FacilityStateTransitionService:
    """Handles side effects of facility state changes."""

    @staticmethod
    def handle_creation(facility):
        """When a new facility is created, log it."""
        logger.info(f"Facility {facility.id} ({facility.name}) created in building {facility.building.name}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            FacilityStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(facility, old_status, new_status):
        """Handle facility status transitions."""
        from communication.services.notification import NotificationService

        # When facility goes into maintenance
        if new_status == 'MNT' and old_status != 'MNT':
            # Notify all active reservations for this facility
            reservations = facility.reservations.filter(
                status__in=['PND', 'APP'],
                start_datetime__gte=timezone.now()
            )
            for reservation in reservations:
                if reservation.reserved_by:
                    NotificationService.create_notification(
                        recipient=reservation.reserved_by,
                        title="Facility Under Maintenance",
                        message=f"The facility '{facility.name}' you reserved is now under maintenance. Please contact admin.",
                        notification_type='ALERT'
                    )
                    # Optionally cancel or postpone reservation
                    reservation.status = 'CNC'
                    reservation.cancellation_reason = "Facility under maintenance"
                    reservation.save()
            logger.info(f"Facility {facility.id} under maintenance, {reservations.count()} reservations affected")

        # When facility becomes available again
        if new_status == 'AVL' and old_status == 'MNT':
            logger.info(f"Facility {facility.id} is now available after maintenance")

        # When facility is closed permanently
        if new_status == 'CLS' and old_status != 'CLS':
            # Cancel all future reservations
            reservations = facility.reservations.filter(
                status__in=['PND', 'APP'],
                start_datetime__gte=timezone.now()
            )
            for reservation in reservations:
                reservation.status = 'CNC'
                reservation.cancellation_reason = "Facility permanently closed"
                reservation.save()
            logger.info(f"Facility {facility.id} closed, {reservations.count()} reservations cancelled")