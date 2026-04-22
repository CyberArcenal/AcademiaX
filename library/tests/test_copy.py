from django.test import TestCase
from datetime import date
from library.models import Author, Publisher, Book, BookCopy
from library.services.copy import BookCopyService
from library.serializers.copy import (
    BookCopyCreateSerializer,
    BookCopyUpdateSerializer,
    BookCopyDisplaySerializer,
)
from common.enums.library import BookStatus


class BookCopyModelTest(TestCase):
    def setUp(self):
        self.publisher = Publisher.objects.create(name="Anvil")
        self.book = Book.objects.create(
            isbn="978-971-27-0000-0",
            title="Noli Me Tangere",
            publisher=self.publisher,
            publication_year=1887
        )

    def test_create_book_copy(self):
        copy = BookCopy.objects.create(
            book=self.book,
            copy_number="Copy 1",
            barcode="BC-001",
            status=BookStatus.AVAILABLE,
            location="Shelf A1",
            acquisition_date=date(2025, 1, 15)
        )
        self.assertEqual(copy.book, self.book)
        self.assertEqual(copy.barcode, "BC-001")

    def test_str_method(self):
        copy = BookCopy.objects.create(book=self.book, copy_number="Copy 2", barcode="BC-002")
        expected = f"{self.book.title} - Copy 2 (BC-002)"
        self.assertEqual(str(copy), expected)


class BookCopyServiceTest(TestCase):
    def setUp(self):
        self.publisher = Publisher.objects.create(name="UP Press")
        self.book = Book.objects.create(
            isbn="978-971-27-0001-7",
            title="El Filibusterismo",
            publisher=self.publisher,
            publication_year=1891,
            total_copies=0,
            available_copies=0
        )

    def test_create_copy(self):
        copy = BookCopyService.create_copy(
            book=self.book,
            copy_number="Copy A",
            barcode="BAR-001",
            status=BookStatus.AVAILABLE,
            location="Shelf B2"
        )
        self.assertEqual(copy.book, self.book)
        self.book.refresh_from_db()
        self.assertEqual(self.book.total_copies, 1)
        self.assertEqual(self.book.available_copies, 1)

    def test_get_available_copies(self):
        BookCopy.objects.create(book=self.book, copy_number="C1", barcode="BC1", status=BookStatus.AVAILABLE)
        BookCopy.objects.create(book=self.book, copy_number="C2", barcode="BC2", status=BookStatus.BORROWED)
        available = BookCopyService.get_available_copies(self.book.id)
        self.assertEqual(available.count(), 1)

    def test_update_status(self):
        copy = BookCopy.objects.create(book=self.book, copy_number="C3", barcode="BC3", status=BookStatus.AVAILABLE)
        updated = BookCopyService.update_status(copy, BookStatus.BORROWED)
        self.assertEqual(updated.status, BookStatus.BORROWED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)


class BookCopySerializerTest(TestCase):
    def setUp(self):
        self.publisher = Publisher.objects.create(name="Anvil")
        self.book = Book.objects.create(
            isbn="1234", title="Test Book", publisher=self.publisher, publication_year=2025
        )

    def test_create_serializer_valid(self):
        data = {
            "book_id": self.book.id,
            "copy_number": "C1",
            "barcode": "BAR123",
            "status": BookStatus.AVAILABLE
        }
        serializer = BookCopyCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        copy = serializer.save()
        self.assertEqual(copy.book, self.book)

    def test_update_serializer(self):
        copy = BookCopy.objects.create(book=self.book, copy_number="C2", barcode="BAR456", status=BookStatus.AVAILABLE)
        data = {"status": BookStatus.DAMAGED, "notes": "Water damage"}
        serializer = BookCopyUpdateSerializer(copy, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, BookStatus.DAMAGED)

    def test_display_serializer(self):
        copy = BookCopy.objects.create(book=self.book, copy_number="C3", barcode="BAR789")
        serializer = BookCopyDisplaySerializer(copy)
        self.assertEqual(serializer.data["copy_number"], "C3")
        self.assertEqual(serializer.data["book"]["id"], self.book.id)