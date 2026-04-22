from django.test import TestCase
from datetime import date
from users.models import User
from teachers.models import Teacher
from classes.models import AcademicYear, GradeLevel, Section, Classroom
from classes.services.section import SectionService
from classes.serializers.section import (
    SectionCreateSerializer,
    SectionUpdateSerializer,
    SectionDisplaySerializer,
)
from common.enums.academic import GradeLevel as GradeLevelChoices


class SectionModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31)
        )
        self.grade_level = GradeLevel.objects.create(
            level=GradeLevelChoices.GRADE_7,
            name="Grade 7",
            order=7
        )
        self.user = User.objects.create_user(username="teacher1", email="t1@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            birth_date="1980-01-01",
            gender="M",
            hire_date="2020-01-01"
        )
        self.classroom = Classroom.objects.create(room_number="101", capacity=40)

    def test_create_section(self):
        section = Section.objects.create(
            name="A",
            grade_level=self.grade_level,
            academic_year=self.academic_year,
            homeroom_teacher=self.teacher,
            classroom=self.classroom,
            capacity=40
        )
        self.assertEqual(section.name, "A")
        self.assertEqual(section.grade_level, self.grade_level)
        self.assertEqual(section.homeroom_teacher, self.teacher)

    def test_str_method(self):
        section = Section.objects.create(
            name="B",
            grade_level=self.grade_level,
            academic_year=self.academic_year
        )
        expected = f"Grade 7 - B (2025-2026)"
        self.assertEqual(str(section), expected)


class SectionServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_8, name="Grade 8", order=8)
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            birth_date="1985-01-01",
            gender="F",
            hire_date="2019-01-01"
        )
        self.classroom = Classroom.objects.create(room_number="201", capacity=45)

    def test_create_section(self):
        section = SectionService.create_section(
            name="C",
            grade_level=self.grade_level,
            academic_year=self.academic_year,
            homeroom_teacher=self.teacher,
            classroom=self.classroom,
            capacity=45
        )
        self.assertEqual(section.name, "C")
        self.assertEqual(section.homeroom_teacher, self.teacher)

    def test_get_sections_by_grade_level(self):
        Section.objects.create(name="A", grade_level=self.grade_level, academic_year=self.academic_year)
        Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        sections = SectionService.get_sections_by_grade_level(self.grade_level.id, self.academic_year.id)
        self.assertEqual(sections.count(), 2)

    def test_update_section(self):
        section = Section.objects.create(name="Old", grade_level=self.grade_level, academic_year=self.academic_year, capacity=30)
        updated = SectionService.update_section(section, {"name": "New", "capacity": 35})
        self.assertEqual(updated.name, "New")
        self.assertEqual(updated.capacity, 35)

    def test_update_enrollment_count(self):
        section = Section.objects.create(name="D", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40, current_enrollment=0)
        # Simulate enrollment (we'd normally create enrollments, but for test we just call method)
        updated = SectionService.update_enrollment_count(section)
        self.assertEqual(updated.current_enrollment, 0)  # No actual enrollments yet
        # But method should work

    def test_get_sections_with_availability(self):
        section = Section.objects.create(name="E", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40, current_enrollment=25)
        availability = SectionService.get_sections_with_availability(self.grade_level.id, self.academic_year.id)
        self.assertEqual(len(availability), 1)
        self.assertEqual(availability[0]['remaining'], 15)


class SectionSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_9, name="Grade 9", order=9)
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Mark",
            last_name="Brown",
            birth_date="1975-01-01",
            gender="M",
            hire_date="2015-01-01"
        )
        self.classroom = Classroom.objects.create(room_number="301", capacity=50)

    def test_create_serializer_valid(self):
        data = {
            "name": "F",
            "grade_level_id": self.grade_level.id,
            "academic_year_id": self.academic_year.id,
            "homeroom_teacher_id": self.teacher.id,
            "classroom_id": self.classroom.id,
            "capacity": 50
        }
        serializer = SectionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        section = serializer.save()
        self.assertEqual(section.grade_level, self.grade_level)

    def test_update_serializer(self):
        section = Section.objects.create(name="Old", grade_level=self.grade_level, academic_year=self.academic_year, capacity=30)
        data = {"name": "Updated", "capacity": 45}
        serializer = SectionUpdateSerializer(section, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")

    def test_display_serializer(self):
        section = Section.objects.create(name="G", grade_level=self.grade_level, academic_year=self.academic_year, capacity=40)
        serializer = SectionDisplaySerializer(section)
        self.assertEqual(serializer.data["name"], "G")
        self.assertEqual(serializer.data["grade_level"]["id"], self.grade_level.id)