from django.test import TestCase
from datetime import date, timedelta
from users.models import User
from students.models import Student
from library.models import Author, Publisher, Book, BookCopy, BorrowTransaction
from library.services.borrow import BorrowTransactionService
from library.serializers.borrow import (
    BorrowTransactionCreateSerializer,
    BorrowTransactionUpdateSerializer,
    BorrowTransactionDisplaySerializer,
)
from common.enums.library import BorrowStatus


class BorrowTransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="librarian", email="lib@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.publisher = Publisher.objects.create(name="Anvil")
        self.book = Book.objects.create(
            isbn="978-971-27-0000-0",
            title="Noli Me Tangere",
            publisher=self.publisher,
            publication_year=1887
        )
        self.copy = BookCopy.objects.create(
            book=self.book, copy_number="C1", barcode="BC-001", status="AVL"
        )

    def test_create_borrow_transaction(self):
        borrow = BorrowTransaction.objects.create(
            copy=self.copy,
            borrower=self.student,
            borrowed_by=self.user,
            borrow_date=date(2025, 1, 15),
            due_date=date(2025, 1, 29),
            status=BorrowStatus.BORROWED
        )
        self.assertEqual(borrow.copy, self.copy)
        self.assertEqual(borrow.borrower, self.student)
        self.assertEqual(borrow.status, BorrowStatus.BORROWED)

    def test_str_method(self):
        borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,1,15), due_date=date(2025,1,29)
        )
        expected = f"{self.student} borrowed {self.book.title} (due 2025-01-29)"
        self.assertEqual(str(borrow), expected)


class BorrowTransactionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="librarian2", email="lib2@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.publisher = Publisher.objects.create(name="UP Press")
        self.book = Book.objects.create(
            isbn="978-971-27-0001-7",
            title="El Filibusterismo",
            publisher=self.publisher,
            publication_year=1891
        )
        self.copy = BookCopy.objects.create(
            book=self.book, copy_number="C2", barcode="BC-002", status="AVL"
        )

    def test_create_borrow(self):
        borrow = BorrowTransactionService.create_borrow(
            copy=self.copy,
            borrower=self.student,
            borrowed_by=self.user,
            borrow_date=date(2025, 2, 1),
            due_date=date(2025, 2, 15)
        )
        self.assertEqual(borrow.status, BorrowStatus.BORROWED)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, "BRW")

    def test_return_book(self):
        borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,2,1), due_date=date(2025,2,15), status=BorrowStatus.BORROWED
        )
        returned = BorrowTransactionService.return_book(borrow, return_date=date(2025, 2, 10), notes="Returned early")
        self.assertEqual(returned.status, BorrowStatus.RETURNED)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, "AVL")

    def test_get_overdue_borrows(self):
        today = date.today()
        overdue = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1), status=BorrowStatus.BORROWED
        )
        not_overdue = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=today - timedelta(days=2),
            due_date=today + timedelta(days=5), status=BorrowStatus.BORROWED
        )
        overdue_list = BorrowTransactionService.get_overdue_borrows()
        self.assertIn(overdue, overdue_list)
        self.assertNotIn(not_overdue, overdue_list)


class BorrowTransactionSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="librarian3", email="lib3@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.publisher = Publisher.objects.create(name="Vibal")
        self.book = Book.objects.create(
            isbn="1234", title="Test Book", publisher=self.publisher, publication_year=2025
        )
        self.copy = BookCopy.objects.create(book=self.book, copy_number="C3", barcode="BC-003", status="AVL")

    def test_create_serializer_valid(self):
        data = {
            "copy_id": self.copy.id,
            "borrower_id": self.student.id,
            "borrowed_by_id": self.user.id,
            "borrow_date": "2025-03-01",
            "due_date": "2025-03-15"
        }
        serializer = BorrowTransactionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        borrow = serializer.save()
        self.assertEqual(borrow.copy, self.copy)

    def test_update_serializer_return(self):
        borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,3,1), due_date=date(2025,3,15), status=BorrowStatus.BORROWED
        )
        data = {"return_date": "2025-03-10", "status": BorrowStatus.RETURNED}
        serializer = BorrowTransactionUpdateSerializer(borrow, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, BorrowStatus.RETURNED)

    def test_display_serializer(self):
        borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,3,1), due_date=date(2025,3,15)
        )
        serializer = BorrowTransactionDisplaySerializer(borrow)
        self.assertEqual(serializer.data["copy"]["id"], self.copy.id)
        self.assertEqual(serializer.data["borrower"]["id"], self.student.id)