from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from enrollments.models import Enrollment
from fees.models import FeeStructure, FeeAssessment, Payment, CollectionReport
from fees.services.collection import CollectionReportService
from fees.serializers.collection import (
    CollectionReportCreateSerializer,
    CollectionReportUpdateSerializer,
    CollectionReportDisplaySerializer,
)
from common.enums.fees import FeeCategory, PaymentMethod


class CollectionReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_collection_report(self):
        report = CollectionReport.objects.create(
            report_date=date(2025, 6, 15),
            total_collections=Decimal('15000.00'),
            total_assessments=Decimal('20000.00'),
            total_outstanding=Decimal('5000.00'),
            payment_method_breakdown={'CASH': 10000, 'CARD': 5000},
            generated_by=self.user,
            notes="Daily summary"
        )
        self.assertEqual(report.report_date, date(2025, 6, 15))
        self.assertEqual(report.total_collections, Decimal('15000.00'))
        self.assertEqual(report.payment_method_breakdown, {'CASH': 10000, 'CARD': 5000})

    def test_str_method(self):
        report = CollectionReport.objects.create(report_date=date(2025, 6, 15))
        expected = "Collection Report - 2025-06-15"
        self.assertEqual(str(report), expected)


class CollectionReportServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="accountant", email="acc@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="A", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.fee_structure = FeeStructure.objects.create(
            name="Tuition", category=FeeCategory.TUITION, amount=Decimal('10000.00'),
            academic_year=self.academic_year
        )
        self.assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=10000, due_date=date(2025,8,15), balance=5000
        )

    def test_generate_daily_report(self):
        # Create payments for today
        Payment.objects.create(
            assessment=self.assessment, amount=3000, payment_date=date.today(),
            payment_method=PaymentMethod.CASH, is_verified=True
        )
        Payment.objects.create(
            assessment=self.assessment, amount=2000, payment_date=date.today(),
            payment_method=PaymentMethod.ONLINE, is_verified=True
        )
        report = CollectionReportService.generate_daily_report(date.today(), self.user)
        self.assertEqual(report.report_date, date.today())
        self.assertEqual(report.total_collections, Decimal('5000.00'))
        self.assertIn('CASH', report.payment_method_breakdown)
        self.assertIn('ONLINE', report.payment_method_breakdown)

    def test_get_report_by_date(self):
        report = CollectionReport.objects.create(report_date=date(2025, 6, 15))
        fetched = CollectionReportService.get_report_by_date(date(2025, 6, 15))
        self.assertEqual(fetched, report)


class CollectionReportSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "report_date": "2025-06-30",
            "generated_by_id": self.user.id,
            "notes": "End of month"
        }
        serializer = CollectionReportCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Note: The actual create method may override totals; but for serializer validation it's fine.
        report = serializer.save()
        self.assertEqual(report.report_date, date(2025, 6, 30))

    def test_update_serializer(self):
        report = CollectionReport.objects.create(report_date=date(2025, 6, 15))
        data = {"notes": "Updated notes"}
        serializer = CollectionReportUpdateSerializer(report, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.notes, "Updated notes")

    def test_display_serializer(self):
        report = CollectionReport.objects.create(report_date=date(2025, 6, 15), total_collections=Decimal('10000.00'))
        serializer = CollectionReportDisplaySerializer(report)
        self.assertEqual(serializer.data["report_date"], "2025-06-15")
        self.assertEqual(serializer.data["total_collections"], "10000.00")