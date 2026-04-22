from django.test import TestCase
from datetime import date, timedelta
from users.models import User
from hr.models import Department, Position, Employee, LeaveRequest
from hr.services.leave import LeaveRequestService
from hr.serializers.leave import (
    LeaveRequestCreateSerializer,
    LeaveRequestUpdateSerializer,
    LeaveRequestDisplaySerializer,
)
from common.enums.hr import LeaveType, LeaveStatus


class LeaveRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp1", email="emp1@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-001", hire_date=date(2025,1,1))

    def test_create_leave_request(self):
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=LeaveType.SICK,
            start_date=date(2025, 6, 10),
            end_date=date(2025, 6, 12),
            days_requested=3,
            reason="Flu",
            status=LeaveStatus.PENDING
        )
        self.assertEqual(leave.employee, self.employee)
        self.assertEqual(leave.leave_type, LeaveType.SICK)
        self.assertEqual(leave.days_requested, 3)

    def test_str_method(self):
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=LeaveType.VACATION,
            start_date=date(2025,7,1),
            end_date=date(2025,7,5),
            days_requested=5
        )
        expected = f"{self.employee} - Vacation (2025-07-01 to 2025-07-05)"
        self.assertEqual(str(leave), expected)


class LeaveRequestServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp2", email="emp2@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-002", hire_date=date(2025,1,1))
        self.approver = Employee.objects.create(
            user=User.objects.create_user(username="mgr", email="mgr@example.com", password="test"),
            employee_number="MGR-001",
            hire_date=date(2020,1,1)
        )

    def test_create_leave_request(self):
        leave = LeaveRequestService.create_leave_request(
            employee=self.employee,
            leave_type=LeaveType.EMERGENCY,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 2),
            reason="Family emergency"
        )
        self.assertEqual(leave.days_requested, 2)
        self.assertEqual(leave.status, LeaveStatus.PENDING)

    def test_get_leaves_by_employee(self):
        LeaveRequest.objects.create(employee=self.employee, leave_type=LeaveType.SICK, start_date=date(2025,5,1), end_date=date(2025,5,1), days_requested=1)
        LeaveRequest.objects.create(employee=self.employee, leave_type=LeaveType.VACATION, start_date=date(2025,6,1), end_date=date(2025,6,5), days_requested=5)
        leaves = LeaveRequestService.get_leaves_by_employee(self.employee.id)
        self.assertEqual(leaves.count(), 2)

    def test_update_leave_status_approve(self):
        leave = LeaveRequest.objects.create(employee=self.employee, leave_type=LeaveType.SICK, start_date=date(2025,9,1), end_date=date(2025,9,1), days_requested=1, status=LeaveStatus.PENDING)
        approved = LeaveRequestService.update_leave_status(leave, LeaveStatus.APPROVED, approved_by=self.approver, remarks="Approved")
        self.assertEqual(approved.status, LeaveStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.approver)
        self.assertIsNotNone(approved.approved_at)


class LeaveRequestSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp3", email="emp3@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-003", hire_date=date(2025,1,1))

    def test_create_serializer_valid(self):
        data = {
            "employee_id": self.employee.id,
            "leave_type": LeaveType.SICK,
            "start_date": "2025-10-01",
            "end_date": "2025-10-03",
            "reason": "Medical appointment"
        }
        serializer = LeaveRequestCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        leave = serializer.save()
        self.assertEqual(leave.employee, self.employee)

    def test_update_serializer(self):
        leave = LeaveRequest.objects.create(employee=self.employee, leave_type=LeaveType.VACATION, start_date=date(2025,11,1), end_date=date(2025,11,5), days_requested=5, status=LeaveStatus.PENDING)
        data = {"status": LeaveStatus.APPROVED, "remarks": "Approved by manager"}
        serializer = LeaveRequestUpdateSerializer(leave, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, LeaveStatus.APPROVED)

    def test_display_serializer(self):
        leave = LeaveRequest.objects.create(employee=self.employee, leave_type=LeaveType.SICK, start_date=date(2025,12,1), end_date=date(2025,12,1), days_requested=1)
        serializer = LeaveRequestDisplaySerializer(leave)
        self.assertEqual(serializer.data["leave_type"], LeaveType.SICK)
        self.assertEqual(serializer.data["employee"]["id"], self.employee.id)