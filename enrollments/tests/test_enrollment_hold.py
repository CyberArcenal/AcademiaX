from django.test import TestCase
from datetime import date
from decimal import Decimal
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from users.models import User
from enrollments.models import Enrollment, EnrollmentHold
from enrollments.services.enrollment_hold import EnrollmentHoldService
from enrollments.serializers.enrollment_hold import (
    EnrollmentHoldCreateSerializer,
    EnrollmentHoldUpdateSerializer,
    EnrollmentHoldDisplaySerializer,
)
from common.enums.enrollment import EnrollmentStatus


class EnrollmentHoldModelTest(TestCase):
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
            grade_level=self.grade_level, section=self.section,
            status=EnrollmentStatus.PENDING
        )

    def test_create_enrollment_hold(self):
        hold = EnrollmentHold.objects.create(
            enrollment=self.enrollment,
            reason="Outstanding balance",
            amount_due=Decimal('5000.00'),
            is_resolved=False
        )
        self.assertEqual(hold.enrollment, self.enrollment)
        self.assertEqual(hold.reason, "Outstanding balance")
        self.assertEqual(hold.amount_due, Decimal('5000.00'))
        self.assertFalse(hold.is_resolved)

    def test_str_method(self):
        hold = EnrollmentHold.objects.create(
            enrollment=self.enrollment,
            reason="Missing documents"
        )
        expected = f"Hold for {self.enrollment} - Missing documents"
        self.assertEqual(str(hold), expected)


class EnrollmentHoldServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="B", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section,
            status=EnrollmentStatus.PENDING
        )
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_hold(self):
        hold = EnrollmentHoldService.create_hold(
            enrollment=self.enrollment,
            reason="Incomplete requirements",
            amount_due=Decimal('2500.00')
        )
        self.assertEqual(hold.enrollment, self.enrollment)
        self.assertFalse(hold.is_resolved)

    def test_prevent_duplicate_active_hold(self):
        EnrollmentHoldService.create_hold(self.enrollment, "First hold")
        with self.assertRaises(Exception):
            EnrollmentHoldService.create_hold(self.enrollment, "Second hold")

    def test_get_hold_by_enrollment(self):
        hold = EnrollmentHold.objects.create(enrollment=self.enrollment, reason="Test hold")
        fetched = EnrollmentHoldService.get_hold_by_enrollment(self.enrollment.id)
        self.assertEqual(fetched, hold)

    def test_resolve_hold(self):
        hold = EnrollmentHold.objects.create(enrollment=self.enrollment, reason="Test hold", is_resolved=False)
        resolved = EnrollmentHoldService.resolve_hold(hold, self.user)
        self.assertTrue(resolved.is_resolved)
        self.assertIsNotNone(resolved.resolved_at)
        self.assertEqual(resolved.resolved_by, self.user)

    def test_update_hold(self):
        hold = EnrollmentHold.objects.create(enrollment=self.enrollment, reason="Old reason", amount_due=Decimal('1000.00'))
        updated = EnrollmentHoldService.update_hold(hold, "New reason", Decimal('2000.00'))
        self.assertEqual(updated.reason, "New reason")
        self.assertEqual(updated.amount_due, Decimal('2000.00'))


class EnrollmentHoldSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="C", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section,
            status=EnrollmentStatus.PENDING
        )

    def test_create_serializer_valid(self):
        data = {
            "enrollment_id": self.enrollment.id,
            "reason": "Financial issue",
            "amount_due": "3000.00"
        }
        serializer = EnrollmentHoldCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        hold = serializer.save()
        self.assertEqual(hold.enrollment, self.enrollment)

    def test_update_serializer(self):
        hold = EnrollmentHold.objects.create(enrollment=self.enrollment, reason="Old", amount_due=Decimal('500.00'))
        data = {"reason": "Updated reason", "amount_due": "750.00"}
        serializer = EnrollmentHoldUpdateSerializer(hold, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.reason, "Updated reason")
        self.assertEqual(updated.amount_due, Decimal('750.00'))

    def test_display_serializer(self):
        hold = EnrollmentHold.objects.create(enrollment=self.enrollment, reason="Test hold")
        serializer = EnrollmentHoldDisplaySerializer(hold)
        self.assertEqual(serializer.data["enrollment"]["id"], self.enrollment.id)
        self.assertEqual(serializer.data["reason"], "Test hold")