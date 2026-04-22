from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from enrollments.models import Enrollment
from fees.models import FeeStructure, FeeAssessment
from fees.services.fee_assessment import FeeAssessmentService
from fees.serializers.fee_assessment import (
    FeeAssessmentCreateSerializer,
    FeeAssessmentUpdateSerializer,
    FeeAssessmentDisplaySerializer,
)
from common.enums.fees import FeeCategory, PaymentStatus


class FeeAssessmentModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="A", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.fee_structure = FeeStructure.objects.create(
            name="Tuition", category=FeeCategory.TUITION, amount=Decimal('10000.00'),
            academic_year=self.academic_year
        )

    def test_create_fee_assessment(self):
        assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment,
            fee_structure=self.fee_structure,
            amount=Decimal('10000.00'),
            due_date=date(2025, 8, 15),
            status=PaymentStatus.PENDING,
            balance=Decimal('10000.00')
        )
        self.assertEqual(assessment.enrollment, self.enrollment)
        self.assertEqual(assessment.amount, Decimal('10000.00'))

    def test_str_method(self):
        assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment,
            fee_structure=self.fee_structure,
            amount=Decimal('5000.00')
        )
        expected = f"{self.enrollment} - Tuition - 5000.00"
        self.assertEqual(str(assessment), expected)


class FeeAssessmentServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.fee_structure = FeeStructure.objects.create(
            name="Misc", category=FeeCategory.OTHER, amount=Decimal('2000.00'),
            academic_year=self.academic_year, due_date=date(2025, 9, 1)
        )

    def test_create_assessment(self):
        assessment = FeeAssessmentService.create_assessment(
            enrollment=self.enrollment,
            fee_structure=self.fee_structure,
            amount=Decimal('2000.00'),
            due_date=date(2025, 9, 1)
        )
        self.assertEqual(assessment.enrollment, self.enrollment)
        self.assertEqual(assessment.balance, Decimal('2000.00'))

    def test_update_balance(self):
        assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=2000, due_date=date(2025,9,1), balance=2000
        )
        updated = FeeAssessmentService.update_balance(assessment, Decimal('500.00'))
        self.assertEqual(updated.balance, Decimal('1500.00'))
        self.assertEqual(updated.status, PaymentStatus.PARTIAL)

    def test_mark_overdue(self):
        past_due = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=1000, due_date=date(2025,1,1), balance=1000, status=PaymentStatus.PENDING
        )
        FeeAssessmentService.mark_overdue()
        past_due.refresh_from_db()
        self.assertEqual(past_due.status, PaymentStatus.OVERDUE)


class FeeAssessmentSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.fee_structure = FeeStructure.objects.create(
            name="Lab Fee", category=FeeCategory.LABORATORY, amount=Decimal('800.00'),
            academic_year=self.academic_year
        )

    def test_create_serializer_valid(self):
        data = {
            "enrollment_id": self.enrollment.id,
            "fee_structure_id": self.fee_structure.id,
            "amount": "800.00",
            "due_date": "2025-10-15"
        }
        serializer = FeeAssessmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        assessment = serializer.save()
        self.assertEqual(assessment.enrollment, self.enrollment)

    def test_update_serializer(self):
        assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=800, due_date=date(2025,10,15), balance=800
        )
        data = {"amount": "750.00", "remarks": "Adjusted"}
        serializer = FeeAssessmentUpdateSerializer(assessment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.amount, Decimal('750.00'))

    def test_display_serializer(self):
        assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=800, due_date=date(2025,10,15)
        )
        serializer = FeeAssessmentDisplaySerializer(assessment)
        self.assertEqual(serializer.data["amount"], "800.00")
        self.assertEqual(serializer.data["enrollment"]["id"], self.enrollment.id)