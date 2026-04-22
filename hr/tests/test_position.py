from django.test import TestCase
from hr.models import Department, Position
from hr.services.position import PositionService
from hr.serializers.position import (
    PositionCreateSerializer,
    PositionUpdateSerializer,
    PositionDisplaySerializer,
)


class PositionModelTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="IT", code="IT")

    def test_create_position(self):
        position = Position.objects.create(
            title="Software Engineer",
            department=self.department,
            salary_grade=5,
            is_active=True
        )
        self.assertEqual(position.title, "Software Engineer")
        self.assertEqual(position.department, self.department)

    def test_str_method(self):
        position = Position.objects.create(title="Manager", department=self.department)
        expected = f"Manager ({self.department.code})"
        self.assertEqual(str(position), expected)


class PositionServiceTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="HR", code="HR")

    def test_create_position(self):
        position = PositionService.create_position(
            title="Recruiter",
            department=self.department,
            salary_grade=3
        )
        self.assertEqual(position.title, "Recruiter")

    def test_get_positions_by_department(self):
        Position.objects.create(title="Analyst", department=self.department)
        Position.objects.create(title="Specialist", department=self.department)
        positions = PositionService.get_positions_by_department(self.department.id)
        self.assertEqual(positions.count(), 2)

    def test_update_position(self):
        position = Position.objects.create(title="Old Title", department=self.department)
        updated = PositionService.update_position(position, {"title": "New Title", "salary_grade": 6})
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.salary_grade, 6)


class PositionSerializerTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Sales", code="SALES")

    def test_create_serializer_valid(self):
        data = {
            "title": "Sales Manager",
            "department_id": self.department.id,
            "salary_grade": 7
        }
        serializer = PositionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        position = serializer.save()
        self.assertEqual(position.department, self.department)

    def test_update_serializer(self):
        position = Position.objects.create(title="Old", department=self.department)
        data = {"title": "Updated", "salary_grade": 8}
        serializer = PositionUpdateSerializer(position, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated")

    def test_display_serializer(self):
        position = Position.objects.create(title="Display", department=self.department)
        serializer = PositionDisplaySerializer(position)
        self.assertEqual(serializer.data["title"], "Display")
        self.assertEqual(serializer.data["department"]["id"], self.department.id)