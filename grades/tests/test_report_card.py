from django.test import TestCase
from decimal import Decimal
from datetime import date
from students.models import Student
from classes.models import AcademicYear, Term
from users.models import User
from grades.models import ReportCard
from grades.services.report_card import ReportCardService
from grades.serializers.report_card import (
    ReportCardCreateSerializer,
    ReportCardUpdateSerializer,
    ReportCardDisplaySerializer,
)


class ReportCardModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.term = Term.objects.create(
            academic_year=self.academic_year, term_type="QTR", term_number=1,
            name="Quarter 1", start_date=date(2025,6,1), end_date=date(2025,8,15)
        )

    def test_create_report_card(self):
        report = ReportCard.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            term=self.term,
            gpa=Decimal('88.50'),
            total_units_earned=Decimal('5.0'),
            honors="With Honors"
        )
        self.assertEqual(report.student, self.student)
        self.assertEqual(report.gpa, Decimal('88.50'))

    def test_str_method(self):
        report = ReportCard.objects.create(
            student=self.student, academic_year=self.academic_year, term=self.term
        )
        expected = f"Report Card - {self.student} - {self.academic_year.name}"
        self.assertEqual(str(report), expected)


class ReportCardServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.term = Term.objects.create(
            academic_year=self.academic_year, term_type="QTR", term_number=1,
            name="Quarter 1", start_date=date(2025,6,1), end_date=date(2025,8,15)
        )

    def test_create_report_card(self):
        report = ReportCardService.create_report_card(
            student=self.student,
            academic_year=self.academic_year,
            term=self.term,
            gpa=Decimal('90.00'),
            honors="With High Honors"
        )
        self.assertEqual(report.student, self.student)

    def test_get_report_card_by_student_term(self):
        report = ReportCard.objects.create(student=self.student, academic_year=self.academic_year, term=self.term)
        fetched = ReportCardService.get_report_card_by_student_term(self.student.id, self.academic_year.id, self.term.id)
        self.assertEqual(fetched, report)

    def test_update_report_card(self):
        report = ReportCard.objects.create(student=self.student, academic_year=self.academic_year, term=self.term, gpa=85)
        updated = ReportCardService.update_report_card(report, {"gpa": "88.00", "honors": "With Honors"})
        self.assertEqual(updated.gpa, Decimal('88.00'))


class ReportCardSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.term = Term.objects.create(
            academic_year=self.academic_year, term_type="QTR", term_number=1,
            name="Quarter 1", start_date=date(2025,6,1), end_date=date(2025,8,15)
        )
        self.user = User.objects.create_user(username="principal", email="p@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "academic_year_id": self.academic_year.id,
            "term_id": self.term.id,
            "gpa": "92.00",
            "honors": "With High Honors",
            "signed_by_id": self.user.id
        }
        serializer = ReportCardCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        report = serializer.save()
        self.assertEqual(report.student, self.student)

    def test_update_serializer(self):
        report = ReportCard.objects.create(student=self.student, academic_year=self.academic_year, term=self.term, gpa=85)
        data = {"gpa": "89.00", "notes": "Excellent performance"}
        serializer = ReportCardUpdateSerializer(report, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.gpa, Decimal('89.00'))

    def test_display_serializer(self):
        report = ReportCard.objects.create(student=self.student, academic_year=self.academic_year, term=self.term, gpa=90)
        serializer = ReportCardDisplaySerializer(report)
        self.assertEqual(serializer.data["gpa"], "90.00")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)