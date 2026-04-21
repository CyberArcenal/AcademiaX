from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List
from decimal import Decimal

from ..models.fine import Fine
from ..models.borrow import BorrowTransaction
from ...users.models import User
from ...common.enums.library import FineStatus

class FineService:
    """Service for Fine model operations"""

    # Default fine rate per day (in currency units)
    DAILY_FINE_RATE = Decimal('5.00')

    @staticmethod
    def create_fine(
        borrow_transaction: BorrowTransaction,
        days_overdue: int,
        rate_per_day: Decimal = DAILY_FINE_RATE
    ) -> Fine:
        try:
            with transaction.atomic():
                amount = rate_per_day * days_overdue
                fine = Fine(
                    borrow_transaction=borrow_transaction,
                    amount=amount,
                    days_overdue=days_overdue,
                    status=FineStatus.PENDING
                )
                fine.full_clean()
                fine.save()
                return fine
        except ValidationError as e:
            raise

    @staticmethod
    def get_fine_by_id(fine_id: int) -> Optional[Fine]:
        try:
            return Fine.objects.get(id=fine_id)
        except Fine.DoesNotExist:
            return None

    @staticmethod
    def get_fine_by_borrow(borrow_id: int) -> Optional[Fine]:
        try:
            return Fine.objects.get(borrow_transaction_id=borrow_id)
        except Fine.DoesNotExist:
            return None

    @staticmethod
    def get_fines_by_borrower(borrower_id: int, unpaid_only: bool = True) -> List[Fine]:
        queryset = Fine.objects.filter(borrow_transaction__borrower_id=borrower_id)
        if unpaid_only:
            queryset = queryset.filter(status=FineStatus.PENDING)
        return queryset

    @staticmethod
    def pay_fine(
        fine: Fine,
        paid_by: User,
        receipt_number: str = "",
        remarks: str = ""
    ) -> Fine:
        fine.status = FineStatus.PAID
        fine.paid_at = timezone.now()
        fine.paid_by = paid_by
        fine.receipt_number = receipt_number
        fine.remarks = remarks
        fine.save()
        return fine

    @staticmethod
    def waive_fine(fine: Fine, remarks: str = "") -> Fine:
        fine.status = FineStatus.WAIVED
        fine.remarks = remarks
        fine.save()
        return fine

    @staticmethod
    def delete_fine(fine: Fine) -> bool:
        try:
            fine.delete()
            return True
        except Exception:
            return False