from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.reservation import FacilityReservation
from ..models.facility import Facility
from ...users.models import User
from ...common.enums.facilities import ReservationStatus

class FacilityReservationService:
    """Service for FacilityReservation model operations"""

    @staticmethod
    def create_reservation(
        facility: Facility,
        reserved_by: User,
        title: str,
        purpose: str,
        start_datetime: datetime,
        end_datetime: datetime,
        attendees_count: int = 0,
        requires_setup: bool = False,
        setup_notes: str = ""
    ) -> FacilityReservation:
        try:
            with transaction.atomic():
                # Check for overlapping reservations
                overlapping = FacilityReservation.objects.filter(
                    facility=facility,
                    status__in=[ReservationStatus.PENDING, ReservationStatus.APPROVED],
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime
                ).exists()
                if overlapping:
                    raise ValidationError("Facility is already reserved for the selected time slot")

                reservation = FacilityReservation(
                    facility=facility,
                    reserved_by=reserved_by,
                    title=title,
                    purpose=purpose,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    attendees_count=attendees_count,
                    requires_setup=requires_setup,
                    setup_notes=setup_notes,
                    status=ReservationStatus.PENDING
                )
                reservation.full_clean()
                reservation.save()
                return reservation
        except ValidationError as e:
            raise

    @staticmethod
    def get_reservation_by_id(reservation_id: int) -> Optional[FacilityReservation]:
        try:
            return FacilityReservation.objects.get(id=reservation_id)
        except FacilityReservation.DoesNotExist:
            return None

    @staticmethod
    def get_reservations_by_facility(facility_id: int, upcoming_only: bool = True) -> List[FacilityReservation]:
        queryset = FacilityReservation.objects.filter(facility_id=facility_id)
        if upcoming_only:
            queryset = queryset.filter(start_datetime__gte=timezone.now())
        return queryset.order_by('start_datetime')

    @staticmethod
    def get_reservations_by_user(user_id: int) -> List[FacilityReservation]:
        return FacilityReservation.objects.filter(reserved_by_id=user_id).order_by('-created_at')

    @staticmethod
    def get_pending_reservations() -> List[FacilityReservation]:
        return FacilityReservation.objects.filter(status=ReservationStatus.PENDING).order_by('start_datetime')

    @staticmethod
    def update_reservation(reservation: FacilityReservation, update_data: Dict[str, Any]) -> FacilityReservation:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(reservation, field):
                        setattr(reservation, field, value)
                reservation.full_clean()
                reservation.save()
                return reservation
        except ValidationError as e:
            raise

    @staticmethod
    def approve_reservation(reservation: FacilityReservation, approved_by: User) -> FacilityReservation:
        reservation.status = ReservationStatus.APPROVED
        reservation.approved_by = approved_by
        reservation.approved_at = timezone.now()
        reservation.save()
        return reservation

    @staticmethod
    def reject_reservation(reservation: FacilityReservation, reason: str) -> FacilityReservation:
        reservation.status = ReservationStatus.REJECTED
        reservation.cancellation_reason = reason
        reservation.save()
        return reservation

    @staticmethod
    def cancel_reservation(reservation: FacilityReservation, reason: str) -> FacilityReservation:
        reservation.status = ReservationStatus.CANCELLED
        reservation.cancellation_reason = reason
        reservation.save()
        return reservation

    @staticmethod
    def delete_reservation(reservation: FacilityReservation) -> bool:
        try:
            reservation.delete()
            return True
        except Exception:
            return False