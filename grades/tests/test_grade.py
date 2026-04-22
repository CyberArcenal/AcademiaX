from django.test import TestCase
from decimal import Decimal
from datetime import date
from students.models import Student
from teachers.models import Teacher
from users.models import User
from academic.models import Subject
from classes.models import AcademicYear, GradeLevel, Section, Term
from enrollments.models import Enrollment
from grades.models import Grade
from grades.services.grade import GradeService
from grades.serializers.grade import (
    GradeCreateSerializer,
    GradeUpdateSerializer,
    GradeDisplaySerializer,
)
from common.enums.grades import GradeStatus


class GradeModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.user = User.objects.create_user(username="teacher", email="t@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            birth_date="1980-01-01", gender="M", hire_date="2020-01-01"
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="A", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.term = Term.objects.create(
            academic_year=self.academic_year, term_type="QTR", term_number=1,
            name="Quarter 1", start_date=date(2025,6,1), end_date=date(2025,8,15)
        )

    def test_create_grade(self):
        grade = Grade.objects.create(
            student=self.student,
            subject=self.subject,
            enrollment=self.enrollment,
            teacher=self.teacher,
            term=self.term,
            percentage=Decimal('85.50'),
            status=GradeStatus.DRAFT
        )
        self.assertEqual(grade.student, self.student)
        self.assertEqual(grade.percentage, Decimal('85.50'))

    def test_str_method(self):
        grade = Grade.objects.create(
            student=self.student, subject=self.subject, enrollment=self.enrollment,
            teacher=self.teacher, term=self.term, percentage=90
        )
        expected = f"{self.student} - {self.subject.code} - 90%"
        self.assertEqual(str(grade), expected)


class GradeServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F")
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Jane", last_name="Smith",
            birth_date="1985-01-01", gender="F", hire_date="2019-01-01"
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.term = Term.objects.create(
            academic_year=self.academic_year, term_type="QTR", term_number=1,
            name="Quarter 1", start_date=date(2025,6,1), end_date=date(2025,8,15)
        )

    def test_create_grade(self):
        grade = GradeService.create_grade(
            student=self.student, subject=self.subject, enrollment=self.enrollment,
            teacher=self.teacher, term=self.term, percentage=88
        )
        self.assertEqual(grade.percentage, Decimal('88.00'))

    def test_get_grades_by_student(self):
        Grade.objects.create(student=self.student, subject=self.subject, enrollment=self.enrollment,
                             teacher=self.teacher, term=self.term, percentage=90)
        Grade.objects.create(student=self.student, subject=Subject.objects.create(code="ENG101", name="English"),
                             enrollment=self.enrollment, teacher=self.teacher, term=self.term, percentage=85)
        grades = GradeService.get_grades_by_student(self.student.id)
        self.assertEqual(grades.count(), 2)

    def test_submit_grade(self):
        grade = Grade.objects.create(student=self.student, subject=self.subject, enrollment=self.enrollment,
                                     teacher=self.teacher, term=self.term, status=GradeStatus.DRAFT)
        submitted = GradeService.submit_grade(grade)
        self.assertEqual(submitted.status, GradeStatus.SUBMITTED)
        self.assertIsNotNone(submitted.graded_at)

    def test_calculate_percentage(self):
        result = GradeService.calculate_percentage(Decimal('45'), Decimal('50'))
        self.assertEqual(result, Decimal('90.00'))


class GradeSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M")
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Mark", last_name="Brown",
            birth_date="1975-01-01", gender="M", hire_date="2015-01-01"
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section
        )
        self.term = Term.objects.create(
            academic_year=self.academic_year, term_type="QTR", term_number=1,
            name="Quarter 1", start_date=date(2025,6,1), end_date=date(2025,8,15)
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "subject_id": self.subject.id,
            "enrollment_id": self.enrollment.id,
            "teacher_id": self.teacher.id,
            "term_id": self.term.id,
            "percentage": "92.50"
        }
        serializer = GradeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        grade = serializer.save()
        self.assertEqual(grade.student, self.student)

    def test_update_serializer(self):
        grade = Grade.objects.create(student=self.student, subject=self.subject, enrollment=self.enrollment,
                                     teacher=self.teacher, term=self.term, percentage=80)
        data = {"percentage": "85.00", "remarks": "Improved"}
        serializer = GradeUpdateSerializer(grade, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.percentage, Decimal('85.00'))

    def test_display_serializer(self):
        grade = Grade.objects.create(student=self.student, subject=self.subject, enrollment=self.enrollment,
                                     teacher=self.teacher, term=self.term, percentage=75)
        serializer = GradeDisplaySerializer(grade)
        self.assertEqual(serializer.data["percentage"], "75.00")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)