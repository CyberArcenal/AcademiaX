from django.test import TestCase
from decimal import Decimal
from datetime import date
from students.models import Student
from academic.models import Subject
from classes.models import AcademicYear, GradeLevel, Section, Term
from enrollments.models import Enrollment
from grades.models import FinalGrade
from grades.services.final_grade import FinalGradeService
from grades.serializers.final_grade import (
    FinalGradeCreateSerializer,
    FinalGradeUpdateSerializer,
    FinalGradeDisplaySerializer,
)
from common.enums.grades import GradeStatus


class FinalGradeModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="A", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )

    def test_create_final_grade(self):
        final = FinalGrade.objects.create(
            student=self.student,
            subject=self.subject,
            enrollment=self.enrollment,
            academic_year=self.academic_year,
            q1_grade=Decimal('85.00'),
            q2_grade=Decimal('88.00'),
            q3_grade=Decimal('90.00'),
            q4_grade=Decimal('92.00'),
            final_grade=Decimal('88.75'),
            status=GradeStatus.DRAFT
        )
        self.assertEqual(final.student, self.student)
        self.assertEqual(final.final_grade, Decimal('88.75'))

    def test_str_method(self):
        final = FinalGrade.objects.create(
            student=self.student,
            subject=self.subject,
            enrollment=self.enrollment,
            academic_year=self.academic_year,
            final_grade=90
        )
        expected = f"{self.student} - {self.subject.code} - Final: 90"
        self.assertEqual(str(final), expected)


class FinalGradeServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F")
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )

    def test_create_final_grade(self):
        final = FinalGradeService.create_final_grade(
            student=self.student,
            subject=self.subject,
            enrollment=self.enrollment,
            academic_year=self.academic_year,
            q1_grade=Decimal('82.00'),
            q2_grade=Decimal('86.00'),
            q3_grade=Decimal('89.00'),
            q4_grade=Decimal('91.00')
        )
        self.assertEqual(final.student, self.student)

    def test_get_final_grades_by_student(self):
        FinalGrade.objects.create(student=self.student, subject=self.subject, enrollment=self.enrollment,
                                  academic_year=self.academic_year, final_grade=85)
        FinalGrade.objects.create(student=self.student, subject=Subject.objects.create(code="ENG101", name="English"),
                                  enrollment=self.enrollment, academic_year=self.academic_year, final_grade=88)
        finals = FinalGradeService.get_final_grades_by_student(self.student.id)
        self.assertEqual(finals.count(), 2)

    def test_compute_final_grade(self):
        final = FinalGrade.objects.create(
            student=self.student, subject=self.subject, enrollment=self.enrollment,
            academic_year=self.academic_year,
            q1_grade=80, q2_grade=85, q3_grade=90, q4_grade=95
        )
        computed = FinalGradeService.compute_final_grade(final)
        self.assertEqual(computed, Decimal('87.50'))


class FinalGradeSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M")
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "subject_id": self.subject.id,
            "enrollment_id": self.enrollment.id,
            "academic_year_id": self.academic_year.id,
            "q1_grade": "82.00",
            "q2_grade": "85.00",
            "q3_grade": "88.00",
            "q4_grade": "90.00"
        }
        serializer = FinalGradeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        final = serializer.save()
        self.assertEqual(final.student, self.student)

    def test_update_serializer(self):
        final = FinalGrade.objects.create(
            student=self.student, subject=self.subject, enrollment=self.enrollment,
            academic_year=self.academic_year, final_grade=80
        )
        data = {"final_grade": "85.00", "status": GradeStatus.APPROVED}
        serializer = FinalGradeUpdateSerializer(final, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.final_grade, Decimal('85.00'))

    def test_display_serializer(self):
        final = FinalGrade.objects.create(
            student=self.student, subject=self.subject, enrollment=self.enrollment,
            academic_year=self.academic_year, final_grade=90
        )
        serializer = FinalGradeDisplaySerializer(final)
        self.assertEqual(serializer.data["final_grade"], "90.00")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)