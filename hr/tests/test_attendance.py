from django.test import TestCase
from datetime import date, time
from users.models import User
from hr.models import Department, Position, Employee, EmployeeAttendance
from hr.services.attendance import EmployeeAttendanceService
from hr.serializers.attendance import (
    EmployeeAttendanceCreateSerializer,
    EmployeeAttendanceUpdateSerializer,
    EmployeeAttendanceDisplaySerializer,
)
from common.enums.hr import AttendanceStatus


class EmployeeAttendanceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp1", email="emp1@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-001", hire_date=date(2025,1,1))

    def test_create_attendance(self):
        attendance = EmployeeAttendance.objects.create(
            employee=self.employee,
            date=date(2025, 6, 15),
            status=AttendanceStatus.PRESENT,
            time_in=time(8, 0),
            time_out=time(17, 0)
        )
        self.assertEqual(attendance.employee, self.employee)
        self.assertEqual(attendance.status, AttendanceStatus.PRESENT)

    def test_str_method(self):
        attendance = EmployeeAttendance.objects.create(
            employee=self.employee,
            date=date(2025, 6, 15),
            status=AttendanceStatus.LATE
        )
        expected = f"{self.employee} - 2025-06-15 - Late"
        self.assertEqual(str(attendance), expected)


class EmployeeAttendanceServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp2", email="emp2@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-002", hire_date=date(2025,1,1))
        self.recorder = Employee.objects.create(
            user=User.objects.create_user(username="hr", email="hr@example.com", password="test"),
            employee_number="HR-001",
            hire_date=date(2020,1,1)
        )

    def test_create_attendance(self):
        attendance = EmployeeAttendanceService.create_attendance(
            employee=self.employee,
            date=date(2025, 6, 20),
            status=AttendanceStatus.PRESENT,
            time_in=time(8, 5),
            late_minutes=5,
            recorded_by=self.recorder
        )
        self.assertEqual(attendance.employee, self.employee)
        self.assertEqual(attendance.late_minutes, 5)

    def test_get_attendance_by_employee(self):
        EmployeeAttendance.objects.create(employee=self.employee, date=date(2025,6,1), status=AttendanceStatus.PRESENT)
        EmployeeAttendance.objects.create(employee=self.employee, date=date(2025,6,2), status=AttendanceStatus.ABSENT)
        attendances = EmployeeAttendanceService.get_attendance_by_employee(self.employee.id)
        self.assertEqual(attendances.count(), 2)

    def test_update_attendance(self):
        attendance = EmployeeAttendance.objects.create(employee=self.employee, date=date(2025,6,10), status=AttendanceStatus.PRESENT)
        updated = EmployeeAttendanceService.update_attendance(attendance, {"status": AttendanceStatus.ABSENT, "remarks": "Called in sick"})
        self.assertEqual(updated.status, AttendanceStatus.ABSENT)


class EmployeeAttendanceSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp3", email="emp3@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-003", hire_date=date(2025,1,1))

    def test_create_serializer_valid(self):
        data = {
            "employee_id": self.employee.id,
            "date": "2025-06-25",
            "status": AttendanceStatus.PRESENT,
            "time_in": "08:00:00",
            "time_out": "17:00:00"
        }
        serializer = EmployeeAttendanceCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        attendance = serializer.save()
        self.assertEqual(attendance.employee, self.employee)

    def test_update_serializer(self):
        attendance = EmployeeAttendance.objects.create(employee=self.employee, date=date(2025,6,25), status=AttendanceStatus.PRESENT)
        data = {"status": AttendanceStatus.ABSENT, "remarks": "No show"}
        serializer = EmployeeAttendanceUpdateSerializer(attendance, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, AttendanceStatus.ABSENT)

    def test_display_serializer(self):
        attendance = EmployeeAttendance.objects.create(employee=self.employee, date=date(2025,6,25), status=AttendanceStatus.PRESENT)
        serializer = EmployeeAttendanceDisplaySerializer(attendance)
        self.assertEqual(serializer.data["status"], AttendanceStatus.PRESENT)
        self.assertEqual(serializer.data["employee"]["id"], self.employee.id)