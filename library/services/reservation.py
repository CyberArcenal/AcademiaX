from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List
from datetime import date, timedelta

from ..models.reservation import Reservation
from ..models.copy import BookCopy
from ...students.models.student import Student
from ...common.enums.library import BookStatus

class ReservationService:
    """Service for Reservation model operations"""

    @staticmethod
    def create_reservation(
        copy: BookCopy,
        student: Student,
        expiry_date: Optional[date] = None
    ) -> Reservation:
        try:
            with transaction.atomic():
                if copy.status not in [BookStatus.AVAILABLE, BookStatus.BORROWED]:
                    raise ValidationError("Book copy cannot be reserved")

                # Check if student already has active reservation for this copy
                existing = Reservation.objects.filter(
                    copy=copy,
                    student=student,
                    is_active=True
                ).first()
                if existing:
                    raise ValidationError("Student already has an active reservation for this copy")

                if not expiry_date:
                    expiry_date = date.today() + timedelta(days=3)

                reservation = Reservation(
                    copy=copy,
                    student=student,
                    expiry_date=expiry_date,
                    is_active=True
                )
                reservation.full_clean()
                reservation.save()
                return reservation
        except ValidationError as e:
            raise

    @staticmethod
    def get_reservation_by_id(reservation_id: int) -> Optional[Reservation]:
        try:
            return Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return None

    @staticmethod
    def get_active_reservations_by_student(student_id: int) -> List[Reservation]:
        return Reservation.objects.filter(student_id=student_id, is_active=True)

    @staticmethod
    def get_active_reservations_by_copy(copy_id: int) -> List[Reservation]:
        return Reservation.objects.filter(copy_id=copy_id, is_active=True).order_by('reservation_date')

    @staticmethod
    def fulfill_reservation(reservation: Reservation) -> Reservation:
        """Mark reservation as fulfilled (when student borrows the book)"""
        reservation.is_active = False
        reservation.fulfilled_at = timezone.now()
        reservation.save()
        return reservation

    @staticmethod
    def cancel_reservation(reservation: Reservation) -> Reservation:
        reservation.is_active = False
        reservation.cancelled_at = timezone.now()
        reservation.save()
        return reservation

    @staticmethod
    def expire_old_reservations() -> int:
        """Expire reservations that are past expiry date"""
        today = date.today()
        count = Reservation.objects.filter(
            is_active=True,
            expiry_date__lt=today
        ).update(is_active=False, cancelled_at=timezone.now())
        return count

    @staticmethod
    def delete_reservation(reservation: Reservation) -> bool:
        try:
            reservation.delete()
            return True
        except Exception:
            return False