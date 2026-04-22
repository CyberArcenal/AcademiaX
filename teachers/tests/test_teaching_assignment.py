from django.test import TestCase
from datetime import date
from users.models import User
from teachers.models import Teacher, TeachingAssignment
from classes.models import AcademicYear, GradeLevel, Section, Term
from academic.models import Subject
from teachers.services.teaching_assignment import TeachingAssignmentService
from teachers.serializers.teaching_assignment import (
    TeachingAssignmentCreateSerializer,
    TeachingAssignmentUpdateSerializer,
    TeachingAssignmentDisplaySerializer,
)


class TeachingAssignmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher", email="t@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1)
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="A", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")

    def test_create_teaching_assignment(self):
        assignment = TeachingAssignment.objects.create(
            teacher=self.teacher,
            section=self.section,
            subject=self.subject,
            academic_year=self.academic_year,
            is_active=True
        )
        self.assertEqual(assignment.teacher, self.teacher)
        self.assertEqual(assignment.section, self.section)
        self.assertTrue(assignment.is_active)

    def test_str_method(self):
        assignment = TeachingAssignment.objects.create(
            teacher=self.teacher, section=self.section, subject=self.subject, academic_year=self.academic_year
        )
        expected = f"{self.teacher} teaches {self.subject.code} to {self.section}"
        self.assertEqual(str(assignment), expected)


class TeachingAssignmentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Jane", last_name="Smith",
            birth_date=date(1985,1,1), gender="F", hire_date=date(2019,1,1)
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="SCI101", name="Biology")

    def test_create_assignment(self):
        assignment = TeachingAssignmentService.create_assignment(
            teacher=self.teacher,
            section=self.section,
            subject=self.subject,
            academic_year=self.academic_year,
            is_active=True
        )
        self.assertEqual(assignment.teacher, self.teacher)

    def test_get_assignments_by_teacher(self):
        TeachingAssignment.objects.create(teacher=self.teacher, section=self.section, subject=self.subject, academic_year=self.academic_year)
        assignments = TeachingAssignmentService.get_assignments_by_teacher(self.teacher.id)
        self.assertEqual(assignments.count(), 1)

    def test_get_teacher_load(self):
        TeachingAssignment.objects.create(teacher=self.teacher, section=self.section, subject=self.subject, academic_year=self.academic_year)
        TeachingAssignment.objects.create(teacher=self.teacher, section=self.section, subject=Subject.objects.create(code="ENG101", name="English"), academic_year=self.academic_year)
        load = TeachingAssignmentService.get_teacher_load(self.teacher.id, self.academic_year.id)
        self.assertEqual(load['total_assignments'], 2)
        self.assertEqual(load['unique_subjects'], 2)


class TeachingAssignmentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Mark", last_name="Brown",
            birth_date=date(1975,1,1), gender="M", hire_date=date(2015,1,1)
        )
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="ENG101", name="English")

    def test_create_serializer_valid(self):
        data = {
            "teacher_id": self.teacher.id,
            "section_id": self.section.id,
            "subject_id": self.subject.id,
            "academic_year_id": self.academic_year.id,
            "is_active": True
        }
        serializer = TeachingAssignmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        assignment = serializer.save()
        self.assertEqual(assignment.teacher, self.teacher)

    def test_update_serializer(self):
        assignment = TeachingAssignment.objects.create(
            teacher=self.teacher, section=self.section, subject=self.subject, academic_year=self.academic_year
        )
        data = {"is_active": False}
        serializer = TeachingAssignmentUpdateSerializer(assignment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertFalse(updated.is_active)

    def test_display_serializer(self):
        assignment = TeachingAssignment.objects.create(
            teacher=self.teacher, section=self.section, subject=self.subject, academic_year=self.academic_year
        )
        serializer = TeachingAssignmentDisplaySerializer(assignment)
        self.assertEqual(serializer.data["teacher"]["id"], self.teacher.id)
        self.assertEqual(serializer.data["section"]["id"], self.section.id)