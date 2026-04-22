from django.test import TestCase
from decimal import Decimal
from datetime import date
from users.models import User
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from enrollments.models import Enrollment
from fees.models import FeeStructure, FeeAssessment, Payment
from fees.services.payment import PaymentService
from fees.serializers.payment import (
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
    PaymentDisplaySerializer,
)
from common.enums.fees import FeeCategory, PaymentStatus, PaymentMethod


class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", email="cashier@example.com", password="test")
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
            amount=10000, due_date=date(2025,8,15), balance=10000
        )

    def test_create_payment(self):
        payment = Payment.objects.create(
            assessment=self.assessment,
            amount=Decimal('5000.00'),
            payment_date=date(2025, 7, 15),
            payment_method=PaymentMethod.CASH,
            reference_number="PAY-001",
            received_by=self.user,
            is_verified=True
        )
        self.assertEqual(payment.assessment, self.assessment)
        self.assertEqual(payment.amount, Decimal('5000.00'))
        self.assertEqual(payment.payment_method, PaymentMethod.CASH)

    def test_str_method(self):
        payment = Payment.objects.create(
            assessment=self.assessment,
            amount=Decimal('2000.00'),
            payment_method=PaymentMethod.ONLINE,
            reference_number="REF123"
        )
        expected = f"Payment REF123 - 2000.00"
        self.assertEqual(str(payment), expected)


class PaymentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier2", email="cashier2@example.com", password="test")
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
            name="Misc", category=FeeCategory.OTHER, amount=Decimal('3000.00'),
            academic_year=self.academic_year
        )
        self.assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=3000, due_date=date(2025,9,1), balance=3000
        )

    def test_process_payment(self):
        payment = PaymentService.process_payment(
            assessment=self.assessment,
            amount=Decimal('1500.00'),
            payment_date=date(2025, 8, 20),
            payment_method=PaymentMethod.CARD,
            received_by=self.user,
            reference_number="CARD-123"
        )
        self.assertEqual(payment.amount, Decimal('1500.00'))
        self.assertEqual(payment.reference_number, "CARD-123")
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.balance, Decimal('1500.00'))
        self.assertEqual(self.assessment.status, PaymentStatus.PARTIAL)

    def test_verify_payment(self):
        payment = Payment.objects.create(
            assessment=self.assessment, amount=1000, payment_date=date(2025,8,10),
            payment_method=PaymentMethod.BANK_TRANSFER, is_verified=False
        )
        verified = PaymentService.verify_payment(payment)
        self.assertTrue(verified.is_verified)

    def test_delete_payment_restores_balance(self):
        payment = Payment.objects.create(
            assessment=self.assessment, amount=1000, payment_date=date(2025,8,10),
            payment_method=PaymentMethod.CASH, is_verified=True
        )
        self.assessment.balance = 2000
        self.assessment.save()
        success = PaymentService.delete_payment(payment)
        self.assertTrue(success)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.balance, 3000)  # original 3000 restored


class PaymentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier3", email="cashier3@example.com", password="test")
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
            name="Library Fee", category=FeeCategory.LIBRARY, amount=Decimal('500.00'),
            academic_year=self.academic_year
        )
        self.assessment = FeeAssessment.objects.create(
            enrollment=self.enrollment, fee_structure=self.fee_structure,
            amount=500, due_date=date(2025,10,1), balance=500
        )

    def test_create_serializer_valid(self):
        data = {
            "assessment_id": self.assessment.id,
            "amount": "200.00",
            "payment_date": "2025-09-15",
            "payment_method": PaymentMethod.CASH,
            "received_by_id": self.user.id
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        payment = serializer.save()
        self.assertEqual(payment.assessment, self.assessment)

    def test_update_serializer(self):
        payment = Payment.objects.create(
            assessment=self.assessment, amount=200, payment_date=date(2025,9,15),
            payment_method=PaymentMethod.CASH, is_verified=False
        )
        data = {"is_verified": True, "notes": "Verified"}
        serializer = PaymentUpdateSerializer(payment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_verified)

    def test_display_serializer(self):
        payment = Payment.objects.create(
            assessment=self.assessment, amount=300, payment_date=date(2025,9,20),
            payment_method=PaymentMethod.ONLINE, reference_number="ON-001"
        )
        serializer = PaymentDisplaySerializer(payment)
        self.assertEqual(serializer.data["amount"], "300.00")
        self.assertEqual(serializer.data["assessment"]["id"], self.assessment.id)