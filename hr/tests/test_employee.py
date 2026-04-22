from django.test import TestCase
from datetime import date
from users.models import User
from hr.models import Department, Position, Employee
from hr.services.employee import EmployeeService
from hr.serializers.employee import (
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    EmployeeDisplaySerializer,
)
from common.enums.hr import EmploymentType, EmploymentStatus


class EmployeeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp1", email="emp1@example.com", password="test")
        self.department = Department.objects.create(name="IT", code="IT")
        self.position = Position.objects.create(title="Developer", department=self.department)

    def test_create_employee(self):
        employee = Employee.objects.create(
            user=self.user,
            employee_number="EMP-001",
            department=self.department,
            position=self.position,
            employment_type=EmploymentType.FULL_TIME,
            status=EmploymentStatus.ACTIVE,
            hire_date=date(2025, 1, 15)
        )
        self.assertEqual(employee.user, self.user)
        self.assertEqual(employee.employee_number, "EMP-001")

    def test_str_method(self):
        employee = Employee.objects.create(user=self.user, employee_number="EMP-001")
        expected = f"EMP-001 - {self.user.get_full_name()}"
        self.assertEqual(str(employee), expected)


class EmployeeServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp2", email="emp2@example.com", password="test")
        self.department = Department.objects.create(name="HR", code="HR")
        self.position = Position.objects.create(title="Manager", department=self.department)

    def test_generate_employee_number(self):
        emp_num = EmployeeService.generate_employee_number()
        self.assertTrue(emp_num.startswith(f"EMP-{date.today().year}"))
        self.assertEqual(len(emp_num), 15)  # "EMP-YYYY-XXXXXX" format

    def test_create_employee(self):
        employee = EmployeeService.create_employee(
            user=self.user,
            hire_date=date(2025, 2, 1),
            department=self.department,
            position=self.position,
            employment_type=EmploymentType.FULL_TIME
        )
        self.assertEqual(employee.user, self.user)
        self.assertIsNotNone(employee.employee_number)

    def test_get_employee_by_user(self):
        created = Employee.objects.create(user=self.user, employee_number="EMP-002", hire_date=date(2025,2,1))
        fetched = EmployeeService.get_employee_by_user(self.user.id)
        self.assertEqual(fetched, created)

    def test_update_status(self):
        employee = Employee.objects.create(user=self.user, employee_number="EMP-003", hire_date=date(2025,2,1), status=EmploymentStatus.ACTIVE)
        updated = EmployeeService.update_status(employee, EmploymentStatus.RESIGNED, resignation_date=date(2025,6,30))
        self.assertEqual(updated.status, EmploymentStatus.RESIGNED)
        self.assertEqual(updated.resignation_date, date(2025,6,30))


class EmployeeSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp3", email="emp3@example.com", password="test")
        self.department = Department.objects.create(name="Finance", code="FIN")
        self.position = Position.objects.create(title="Accountant", department=self.department)

    def test_create_serializer_valid(self):
        data = {
            "user_id": self.user.id,
            "hire_date": "2025-03-01",
            "department_id": self.department.id,
            "position_id": self.position.id,
            "employment_type": EmploymentType.FULL_TIME
        }
        serializer = EmployeeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        employee = serializer.save()
        self.assertEqual(employee.user, self.user)

    def test_update_serializer(self):
        employee = Employee.objects.create(user=self.user, employee_number="EMP-004", hire_date=date(2025,3,1))
        data = {"department_id": self.department.id, "position_id": self.position.id, "status": EmploymentStatus.ACTIVE}
        serializer = EmployeeUpdateSerializer(employee, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.department, self.department)

    def test_display_serializer(self):
        employee = Employee.objects.create(user=self.user, employee_number="EMP-005", hire_date=date(2025,3,1))
        serializer = EmployeeDisplaySerializer(employee)
        self.assertEqual(serializer.data["employee_number"], "EMP-005")
        self.assertEqual(serializer.data["user"]["id"], self.user.id)