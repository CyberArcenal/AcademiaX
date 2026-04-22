from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from students.models import Student
from library.models import Author, Publisher, Book, BookCopy, BorrowTransaction, Fine
from library.services.fine import FineService
from library.serializers.fine import (
    FineCreateSerializer,
    FineUpdateSerializer,
    FineDisplaySerializer,
)
from common.enums.library import FineStatus


class FineModelTest(TestCase):
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
        self.copy = BookCopy.objects.create(book=self.book, copy_number="C1", barcode="BC-001", status="AVL")
        self.borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,1,1), due_date=date(2025,1,15)
        )

    def test_create_fine(self):
        fine = Fine.objects.create(
            borrow_transaction=self.borrow,
            amount=Decimal('50.00'),
            days_overdue=5,
            status=FineStatus.PENDING
        )
        self.assertEqual(fine.borrow_transaction, self.borrow)
        self.assertEqual(fine.amount, Decimal('50.00'))

    def test_str_method(self):
        fine = Fine.objects.create(borrow_transaction=self.borrow, amount=Decimal('75.00'))
        expected = f"Fine for {self.borrow}: 75.00"
        self.assertEqual(str(fine), expected)


class FineServiceTest(TestCase):
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
        self.copy = BookCopy.objects.create(book=self.book, copy_number="C2", barcode="BC-002", status="AVL")
        self.borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,2,1), due_date=date(2025,2,15)
        )

    def test_create_fine(self):
        fine = FineService.create_fine(self.borrow, days_overdue=3, rate_per_day=Decimal('10.00'))
        self.assertEqual(fine.amount, Decimal('30.00'))
        self.assertEqual(fine.days_overdue, 3)

    def test_get_fine_by_borrow(self):
        fine = Fine.objects.create(borrow_transaction=self.borrow, amount=40, days_overdue=4)
        fetched = FineService.get_fine_by_borrow(self.borrow.id)
        self.assertEqual(fetched, fine)

    def test_pay_fine(self):
        fine = Fine.objects.create(borrow_transaction=self.borrow, amount=60, days_overdue=6, status=FineStatus.PENDING)
        paid = FineService.pay_fine(fine, paid_by=self.user, receipt_number="RCP-001", remarks="Paid")
        self.assertEqual(paid.status, FineStatus.PAID)
        self.assertIsNotNone(paid.paid_at)

    def test_waive_fine(self):
        fine = Fine.objects.create(borrow_transaction=self.borrow, amount=25, days_overdue=2, status=FineStatus.PENDING)
        waived = FineService.waive_fine(fine, remarks="First offense")
        self.assertEqual(waived.status, FineStatus.WAIVED)


class FineSerializerTest(TestCase):
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
        self.borrow = BorrowTransaction.objects.create(
            copy=self.copy, borrower=self.student, borrow_date=date(2025,3,1), due_date=date(2025,3,15)
        )

    def test_create_serializer_valid(self):
        data = {
            "borrow_transaction_id": self.borrow.id,
            "amount": "45.00",
            "days_overdue": 3
        }
        serializer = FineCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        fine = serializer.save()
        self.assertEqual(fine.borrow_transaction, self.borrow)

    def test_update_serializer_pay(self):
        fine = Fine.objects.create(borrow_transaction=self.borrow, amount=30, days_overdue=2, status=FineStatus.PENDING)
        data = {"status": FineStatus.PAID, "paid_by_id": self.user.id, "receipt_number": "PAY-001"}
        serializer = FineUpdateSerializer(fine, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, FineStatus.PAID)

    def test_display_serializer(self):
        fine = Fine.objects.create(borrow_transaction=self.borrow, amount=50, days_overdue=5)
        serializer = FineDisplaySerializer(fine)
        self.assertEqual(serializer.data["amount"], "50.00")
        self.assertEqual(serializer.data["borrow_transaction"]["id"], self.borrow.id)