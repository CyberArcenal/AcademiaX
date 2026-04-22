from django.test import TestCase
from users.models import User
from hr.models import Department, Employee
from hr.services.department import DepartmentService
from hr.serializers.department import (
    DepartmentCreateSerializer,
    DepartmentUpdateSerializer,
    DepartmentDisplaySerializer,
)


class DepartmentModelTest(TestCase):
    def test_create_department(self):
        dept = Department.objects.create(
            name="Human Resources",
            code="HR",
            description="Handles personnel"
        )
        self.assertEqual(dept.name, "Human Resources")
        self.assertEqual(dept.code, "HR")

    def test_code_uppercase_auto(self):
        dept = Department.objects.create(name="IT", code="it")
        self.assertEqual(dept.code, "IT")

    def test_str_method(self):
        dept = Department.objects.create(name="Finance", code="FIN")
        self.assertEqual(str(dept), "Finance")


class DepartmentServiceTest(TestCase):
    def test_create_department(self):
        dept = DepartmentService.create_department(
            name="Marketing",
            code="MKT",
            description="Marketing and sales"
        )
        self.assertEqual(dept.name, "Marketing")

    def test_get_department_by_code(self):
        created = Department.objects.create(name="R&D", code="RD")
        fetched = DepartmentService.get_department_by_code("rd")
        self.assertEqual(fetched, created)

    def test_update_department(self):
        dept = Department.objects.create(name="Old", code="OLD")
        updated = DepartmentService.update_department(dept, {"name": "New", "is_active": False})
        self.assertEqual(updated.name, "New")
        self.assertFalse(updated.is_active)


class DepartmentSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": "Operations",
            "code": "OPS",
            "description": "Operations department"
        }
        serializer = DepartmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        dept = serializer.save()
        self.assertEqual(dept.name, "Operations")

    def test_update_serializer(self):
        dept = Department.objects.create(name="Old", code="OLD")
        data = {"name": "Updated", "is_active": False}
        serializer = DepartmentUpdateSerializer(dept, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")

    def test_display_serializer(self):
        dept = Department.objects.create(name="Display", code="DISP")
        serializer = DepartmentDisplaySerializer(dept)
        self.assertEqual(serializer.data["name"], "Display")