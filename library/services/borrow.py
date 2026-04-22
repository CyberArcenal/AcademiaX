from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import date, timedelta

from ..models.borrow import BorrowTransaction
from ..models.copy import BookCopy
from students.models.student import Student
from users.models import User
from common.enums.library import BookStatus, BorrowStatus

class BorrowTransactionService:
    """Service for BorrowTransaction model operations"""

    @staticmethod
    def create_borrow(
        copy: BookCopy,
        borrower: Student,
        borrowed_by: User,
        borrow_date: date,
        due_date: Optional[date] = None,
        notes: str = ""
    ) -> BorrowTransaction:
        try:
            with transaction.atomic():
                if copy.status != BookStatus.AVAILABLE:
                    raise ValidationError("Book copy is not available for borrowing")

                if not due_date:
                    # Default due date: 14 days from borrow date
                    due_date = borrow_date + timedelta(days=14)

                transaction_obj = BorrowTransaction(
                    copy=copy,
                    borrower=borrower,
                    borrowed_by=borrowed_by,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    status=BorrowStatus.BORROWED,
                    notes=notes
                )
                transaction_obj.full_clean()
                transaction_obj.save()

                # Update copy status
                from .copy import BookCopyService
                BookCopyService.update_status(copy, BookStatus.BORROWED)
                return transaction_obj
        except ValidationError as e:
            raise

    @staticmethod
    def get_borrow_by_id(borrow_id: int) -> Optional[BorrowTransaction]:
        try:
            return BorrowTransaction.objects.get(id=borrow_id)
        except BorrowTransaction.DoesNotExist:
            return None

    @staticmethod
    def get_borrows_by_borrower(borrower_id: int, active_only: bool = True) -> List[BorrowTransaction]:
        queryset = BorrowTransaction.objects.filter(borrower_id=borrower_id)
        if active_only:
            queryset = queryset.filter(status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE])
        return queryset.order_by('-borrow_date')

    @staticmethod
    def get_overdue_borrows() -> List[BorrowTransaction]:
        today = date.today()
        return BorrowTransaction.objects.filter(
            due_date__lt=today,
            status=BorrowStatus.BORROWED
        )

    @staticmethod
    def return_book(
        borrow: BorrowTransaction,
        return_date: date,
        notes: str = ""
    ) -> BorrowTransaction:
        try:
            with transaction.atomic():
                borrow.return_date = return_date
                borrow.status = BorrowStatus.RETURNED
                borrow.notes = notes
                borrow.save()

                # Update copy status
                from .copy import BookCopyService
                BookCopyService.update_status(borrow.copy, BookStatus.AVAILABLE)

                # Check for overdue fine
                if return_date > borrow.due_date:
                    days_overdue = (return_date - borrow.due_date).days
                    from .fine import FineService
                    FineService.create_fine(borrow, days_overdue)

                return borrow
        except ValidationError as e:
            raise

    @staticmethod
    def renew_borrow(borrow: BorrowTransaction, new_due_date: date) -> BorrowTransaction:
        borrow.due_date = new_due_date
        borrow.renewed_count += 1
        borrow.save()
        return borrow

    @staticmethod
    def delete_borrow(borrow: BorrowTransaction) -> bool:
        try:
            # Restore copy status before deletion
            from .copy import BookCopyService
            BookCopyService.update_status(borrow.copy, BookStatus.AVAILABLE)
            borrow.delete()
            return True
        except Exception:
            return False