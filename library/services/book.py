from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.book import Book
from ..models.author import Author
from ..models.publisher import Publisher

class BookService:
    """Service for Book model operations"""

    @staticmethod
    def create_book(
        isbn: str,
        title: str,
        publisher: Publisher,
        publication_year: int,
        authors: List[Author],
        subtitle: str = "",
        edition: str = "",
        language: str = "English",
        pages: Optional[int] = None,
        description: str = "",
        cover_image_url: str = "",
        dewey_decimal: str = "",
        subject: str = "",
        total_copies: int = 0,
        available_copies: int = 0
    ) -> Book:
        try:
            with transaction.atomic():
                book = Book(
                    isbn=isbn,
                    title=title,
                    subtitle=subtitle,
                    publisher=publisher,
                    publication_year=publication_year,
                    edition=edition,
                    language=language,
                    pages=pages,
                    description=description,
                    cover_image_url=cover_image_url,
                    dewey_decimal=dewey_decimal,
                    subject=subject,
                    total_copies=total_copies,
                    available_copies=available_copies
                )
                book.full_clean()
                book.save()
                book.authors.set(authors)
                return book
        except ValidationError as e:
            raise

    @staticmethod
    def get_book_by_id(book_id: int) -> Optional[Book]:
        try:
            return Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return None

    @staticmethod
    def get_book_by_isbn(isbn: str) -> Optional[Book]:
        try:
            return Book.objects.get(isbn=isbn)
        except Book.DoesNotExist:
            return None

    @staticmethod
    def get_all_books(limit: int = 100) -> List[Book]:
        return Book.objects.all().order_by('title')[:limit]

    @staticmethod
    def update_book(book: Book, update_data: Dict[str, Any]) -> Book:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(book, field) and field != 'authors':
                        setattr(book, field, value)
                book.full_clean()
                book.save()
                if 'authors' in update_data:
                    book.authors.set(update_data['authors'])
                return book
        except ValidationError as e:
            raise

    @staticmethod
    def delete_book(book: Book, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                book.is_active = False
                book.save()
            else:
                book.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_books(query: str, limit: int = 20) -> List[Book]:
        from django.db import models
        return Book.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(isbn__icontains=query) |
            models.Q(subject__icontains=query) |
            models.Q(authors__first_name__icontains=query) |
            models.Q(authors__last_name__icontains=query)
        ).distinct()[:limit]

    @staticmethod
    def get_books_by_author(author_id: int) -> List[Book]:
        return Book.objects.filter(authors__id=author_id)

    @staticmethod
    def update_copies_count(book: Book) -> Book:
        """Update total_copies and available_copies based on actual copies"""
        copies = book.copies.all()
        book.total_copies = copies.count()
        book.available_copies = copies.filter(status='AVL').count()
        book.save()
        return book