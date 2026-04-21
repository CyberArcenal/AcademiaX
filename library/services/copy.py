from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.copy import BookCopy
from ..models.book import Book
from ...common.enums.library import BookStatus

class BookCopyService:
    """Service for BookCopy model operations"""

    @staticmethod
    def create_copy(
        book: Book,
        copy_number: str,
        barcode: str,
        status: str = BookStatus.AVAILABLE,
        location: str = "",
        acquisition_date: Optional[date] = None,
        purchase_price: Optional[float] = None,
        notes: str = ""
    ) -> BookCopy:
        try:
            with transaction.atomic():
                copy = BookCopy(
                    book=book,
                    copy_number=copy_number,
                    barcode=barcode,
                    status=status,
                    location=location,
                    acquisition_date=acquisition_date,
                    purchase_price=purchase_price,
                    notes=notes
                )
                copy.full_clean()
                copy.save()
                # Update book counts
                from .book import BookService
                BookService.update_copies_count(book)
                return copy
        except ValidationError as e:
            raise

    @staticmethod
    def get_copy_by_id(copy_id: int) -> Optional[BookCopy]:
        try:
            return BookCopy.objects.get(id=copy_id)
        except BookCopy.DoesNotExist:
            return None

    @staticmethod
    def get_copy_by_barcode(barcode: str) -> Optional[BookCopy]:
        try:
            return BookCopy.objects.get(barcode=barcode)
        except BookCopy.DoesNotExist:
            return None

    @staticmethod
    def get_copies_by_book(book_id: int) -> List[BookCopy]:
        return BookCopy.objects.filter(book_id=book_id)

    @staticmethod
    def get_available_copies(book_id: int) -> List[BookCopy]:
        return BookCopy.objects.filter(book_id=book_id, status=BookStatus.AVAILABLE)

    @staticmethod
    def update_copy(copy: BookCopy, update_data: Dict[str, Any]) -> BookCopy:
        try:
            with transaction.atomic():
                old_status = copy.status
                for field, value in update_data.items():
                    if hasattr(copy, field):
                        setattr(copy, field, value)
                copy.full_clean()
                copy.save()
                if old_status != copy.status:
                    from .book import BookService
                    BookService.update_copies_count(copy.book)
                return copy
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(copy: BookCopy, status: str) -> BookCopy:
        copy.status = status
        copy.save()
        from .book import BookService
        BookService.update_copies_count(copy.book)
        return copy

    @staticmethod
    def delete_copy(copy: BookCopy) -> bool:
        try:
            book = copy.book
            copy.delete()
            from .book import BookService
            BookService.update_copies_count(book)
            return True
        except Exception:
            return False