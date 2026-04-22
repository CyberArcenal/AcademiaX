from django.test import TestCase
from datetime import date
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from users.models import User
from enrollments.models import Enrollment
from enrollments.services.enrollment import EnrollmentService
from enrollments.serializers.enrollment import (
    EnrollmentCreateSerializer,
    EnrollmentUpdateSerializer,
    EnrollmentDisplaySerializer,
)
from common.enums.enrollment import EnrollmentStatus, EnrollmentPaymentStatus


class EnrollmentModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="A", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40
        )

    def test_create_enrollment(self):
        enrollment = Enrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            section=self.section,
            status=EnrollmentStatus.PENDING,
            enrollment_date=date(2025,6,1)
        )
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.status, EnrollmentStatus.PENDING)

    def test_str_method(self):
        enrollment = Enrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            section=self.section
        )
        expected = f"{self.student} - {self.academic_year.name} - Pending"
        self.assertEqual(str(enrollment), expected)


class EnrollmentServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="B", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40
        )
        self.user = User.objects.create_user(username="registrar", email="reg@example.com", password="test")

    def test_create_enrollment(self):
        enrollment = EnrollmentService.create_enrollment(
            student=self.student,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            section=self.section,
            processed_by=self.user
        )
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.status, EnrollmentStatus.PENDING)
        self.assertEqual(self.section.current_enrollment, 1)

    def test_prevent_duplicate_enrollment(self):
        EnrollmentService.create_enrollment(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        with self.assertRaises(Exception):
            EnrollmentService.create_enrollment(
                student=self.student, academic_year=self.academic_year,
                grade_level=self.grade_level, section=self.section
            )

    def test_update_status_to_enrolled(self):
        enrollment = EnrollmentService.create_enrollment(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        updated = EnrollmentService.update_status(enrollment, EnrollmentStatus.ENROLLED)
        self.assertEqual(updated.status, EnrollmentStatus.ENROLLED)

    def test_transfer_section(self):
        enrollment = EnrollmentService.create_enrollment(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        new_section = Section.objects.create(
            name="C", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40
        )
        transferred = EnrollmentService.transfer_section(enrollment, new_section)
        self.assertEqual(transferred.section, new_section)
        self.assertEqual(self.section.current_enrollment, 0)
        self.assertEqual(new_section.current_enrollment, 1)


class EnrollmentSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="D", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "academic_year_id": self.academic_year.id,
            "grade_level_id": self.grade_level.id,
            "section_id": self.section.id
        }
        serializer = EnrollmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        enrollment = serializer.save()
        self.assertEqual(enrollment.student, self.student)

    def test_update_serializer(self):
        enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        data = {"status": EnrollmentStatus.ENROLLED, "remarks": "Approved"}
        serializer = EnrollmentUpdateSerializer(enrollment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, EnrollmentStatus.ENROLLED)

    def test_display_serializer(self):
        enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        serializer = EnrollmentDisplaySerializer(enrollment)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)
        self.assertEqual(serializer.data["academic_year"]["id"], self.academic_year.id)