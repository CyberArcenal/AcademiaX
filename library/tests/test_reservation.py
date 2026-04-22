from django.test import TestCase
from datetime import date, timedelta
from users.models import User
from students.models import Student
from library.models import Author, Publisher, Book, BookCopy, Reservation
from library.services.reservation import ReservationService
from library.serializers.reservation import (
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationDisplaySerializer,
)
from common.enums.library import BookStatus


class ReservationModelTest(TestCase):
    def setUp(self):
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
            book=self.book, copy_number="C1", barcode="BC-001", status=BookStatus.BORROWED
        )

    def test_create_reservation(self):
        reservation = Reservation.objects.create(
            copy=self.copy,
            student=self.student,
            expiry_date=date(2025, 1, 20),
            is_active=True
        )
        self.assertEqual(reservation.copy, self.copy)
        self.assertEqual(reservation.student, self.student)

    def test_str_method(self):
        reservation = Reservation.objects.create(copy=self.copy, student=self.student)
        expected = f"Reservation by {self.student} for {self.book.title}"
        self.assertEqual(str(reservation), expected)


class ReservationServiceTest(TestCase):
    def setUp(self):
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
            book=self.book, copy_number="C2", barcode="BC-002", status=BookStatus.BORROWED
        )

    def test_create_reservation(self):
        reservation = ReservationService.create_reservation(
            copy=self.copy,
            student=self.student,
            expiry_date=date(2025, 2, 10)
        )
        self.assertEqual(reservation.copy, self.copy)
        self.assertTrue(reservation.is_active)

    def test_get_active_reservations_by_student(self):
        Reservation.objects.create(copy=self.copy, student=self.student, is_active=True)
        Reservation.objects.create(copy=self.copy, student=self.student, is_active=False)
        active = ReservationService.get_active_reservations_by_student(self.student.id)
        self.assertEqual(active.count(), 1)

    def test_cancel_reservation(self):
        reservation = Reservation.objects.create(copy=self.copy, student=self.student, is_active=True)
        cancelled = ReservationService.cancel_reservation(reservation)
        self.assertFalse(cancelled.is_active)
        self.assertIsNotNone(cancelled.cancelled_at)

    def test_fulfill_reservation(self):
        reservation = Reservation.objects.create(copy=self.copy, student=self.student, is_active=True)
        fulfilled = ReservationService.fulfill_reservation(reservation)
        self.assertFalse(fulfilled.is_active)
        self.assertIsNotNone(fulfilled.fulfilled_at)


class ReservationSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.publisher = Publisher.objects.create(name="Vibal")
        self.book = Book.objects.create(
            isbn="1234", title="Test Book", publisher=self.publisher, publication_year=2025
        )
        self.copy = BookCopy.objects.create(book=self.book, copy_number="C3", barcode="BC-003", status=BookStatus.BORROWED)

    def test_create_serializer_valid(self):
        data = {
            "copy_id": self.copy.id,
            "student_id": self.student.id,
            "expiry_date": "2025-03-20"
        }
        serializer = ReservationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        reservation = serializer.save()
        self.assertEqual(reservation.copy, self.copy)

    def test_update_serializer_cancel(self):
        reservation = Reservation.objects.create(copy=self.copy, student=self.student, is_active=True)
        data = {"is_active": False}
        serializer = ReservationUpdateSerializer(reservation, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertFalse(updated.is_active)

    def test_display_serializer(self):
        reservation = Reservation.objects.create(copy=self.copy, student=self.student)
        serializer = ReservationDisplaySerializer(reservation)
        self.assertEqual(serializer.data["copy"]["id"], self.copy.id)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)