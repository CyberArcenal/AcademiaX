from django.test import TestCase
from datetime import date
from decimal import Decimal
from students.models import Student
from teachers.models import Teacher
from users.models import User
from classes.models import AcademicYear, GradeLevel, Section
from academic.models import Subject
from enrollments.models import Enrollment, SubjectEnrollment
from enrollments.services.subject_enrollment import SubjectEnrollmentService
from enrollments.serializers.subject_enrollment import (
    SubjectEnrollmentCreateSerializer,
    SubjectEnrollmentUpdateSerializer,
    SubjectEnrollmentDisplaySerializer,
)
from common.enums.enrollment import EnrollmentStatus


class SubjectEnrollmentModelTest(TestCase):
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
            status=EnrollmentStatus.ENROLLED
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.user = User.objects.create_user(username="teacher1", email="t1@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            birth_date="1980-01-01", gender="M", hire_date="2020-01-01"
        )

    def test_create_subject_enrollment(self):
        se = SubjectEnrollment.objects.create(
            enrollment=self.enrollment,
            subject=self.subject,
            teacher=self.teacher,
            is_dropped=False
        )
        self.assertEqual(se.enrollment, self.enrollment)
        self.assertEqual(se.subject, self.subject)
        self.assertFalse(se.is_dropped)

    def test_str_method(self):
        se = SubjectEnrollment.objects.create(
            enrollment=self.enrollment,
            subject=self.subject
        )
        expected = f"{self.student} - {self.subject.code}"
        self.assertEqual(str(se), expected)


class SubjectEnrollmentServiceTest(TestCase):
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
            status=EnrollmentStatus.ENROLLED
        )
        self.subject1 = Subject.objects.create(code="SCI101", name="Biology")
        self.subject2 = Subject.objects.create(code="SCI102", name="Chemistry")
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Jane", last_name="Smith",
            birth_date="1985-01-01", gender="F", hire_date="2019-01-01"
        )

    def test_enroll_subject(self):
        se = SubjectEnrollmentService.enroll_subject(
            enrollment=self.enrollment,
            subject=self.subject1,
            teacher=self.teacher
        )
        self.assertEqual(se.enrollment, self.enrollment)
        self.assertEqual(se.subject, self.subject1)

    def test_prevent_duplicate_subject_enrollment(self):
        SubjectEnrollment.objects.create(enrollment=self.enrollment, subject=self.subject1)
        with self.assertRaises(Exception):
            SubjectEnrollmentService.enroll_subject(self.enrollment, self.subject1)

    def test_drop_subject(self):
        se = SubjectEnrollment.objects.create(enrollment=self.enrollment, subject=self.subject1)
        dropped = SubjectEnrollmentService.drop_subject(se, reason="Schedule conflict")
        self.assertTrue(dropped.is_dropped)
        self.assertIsNotNone(dropped.drop_date)
        self.assertEqual(dropped.drop_reason, "Schedule conflict")

    def test_update_final_grade(self):
        se = SubjectEnrollment.objects.create(enrollment=self.enrollment, subject=self.subject1)
        updated = SubjectEnrollmentService.update_final_grade(se, Decimal('85.50'))
        self.assertEqual(updated.final_grade, Decimal('85.50'))


class SubjectEnrollmentSerializerTest(TestCase):
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
            status=EnrollmentStatus.ENROLLED
        )
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Mark", last_name="Brown",
            birth_date="1975-01-01", gender="M", hire_date="2015-01-01"
        )

    def test_create_serializer_valid(self):
        data = {
            "enrollment_id": self.enrollment.id,
            "subject_id": self.subject.id,
            "teacher_id": self.teacher.id
        }
        serializer = SubjectEnrollmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        se = serializer.save()
        self.assertEqual(se.enrollment, self.enrollment)

    def test_update_serializer(self):
        se = SubjectEnrollment.objects.create(enrollment=self.enrollment, subject=self.subject)
        data = {"is_dropped": True, "drop_reason": "Overload"}
        serializer = SubjectEnrollmentUpdateSerializer(se, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_dropped)

    def test_display_serializer(self):
        se = SubjectEnrollment.objects.create(enrollment=self.enrollment, subject=self.subject, teacher=self.teacher)
        serializer = SubjectEnrollmentDisplaySerializer(se)
        self.assertEqual(serializer.data["enrollment"]["id"], self.enrollment.id)
        self.assertEqual(serializer.data["subject"]["id"], self.subject.id)