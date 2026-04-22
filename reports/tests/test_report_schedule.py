from django.test import TestCase
from users.models import User
from reports.models import ReportSchedule
from reports.services.report_schedule import ReportScheduleService
from reports.serializers.report_schedule import (
    ReportScheduleCreateSerializer,
    ReportScheduleUpdateSerializer,
    ReportScheduleDisplaySerializer,
)
from common.enums.reports import ReportType, ReportFormat


class ReportScheduleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_schedule(self):
        schedule = ReportSchedule.objects.create(
            name="Daily Attendance Report",
            report_type=ReportType.ATTENDANCE_SUMMARY,
            format=ReportFormat.PDF,
            parameters={"section_id": 1},
            cron_expression="0 8 * * *",
            recipients=["admin@example.com"],
            is_active=True,
            created_by=self.user
        )
        self.assertEqual(schedule.name, "Daily Attendance Report")
        self.assertEqual(schedule.cron_expression, "0 8 * * *")

    def test_str_method(self):
        schedule = ReportSchedule.objects.create(name="Test Schedule", cron_expression="0 0 * * *")
        self.assertEqual(str(schedule), "Test Schedule - 0 0 * * *")


class ReportScheduleServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")

    def test_create_schedule(self):
        schedule = ReportScheduleService.create_schedule(
            name="Weekly Report",
            report_type=ReportType.ENROLLMENT_REPORT,
            format=ReportFormat.EXCEL,
            cron_expression="0 9 * * 1",
            recipients=["admin@example.com"],
            created_by=self.user
        )
        self.assertEqual(schedule.name, "Weekly Report")

    def test_get_active_schedules(self):
        ReportSchedule.objects.create(name="Active1", cron_expression="* * * * *", is_active=True)
        ReportSchedule.objects.create(name="Inactive", cron_expression="* * * * *", is_active=False)
        active = ReportScheduleService.get_active_schedules()
        self.assertEqual(active.count(), 1)


class ReportScheduleSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", email="admin3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "name": "Monthly Report",
            "report_type": ReportType.FINANCIAL_STATEMENT,
            "format": ReportFormat.PDF,
            "cron_expression": "0 0 1 * *",
            "recipients": ["finance@example.com"],
            "created_by_id": self.user.id
        }
        serializer = ReportScheduleCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        schedule = serializer.save()
        self.assertEqual(schedule.name, "Monthly Report")

    def test_update_serializer(self):
        schedule = ReportSchedule.objects.create(name="Old", cron_expression="0 0 * * *", is_active=True)
        data = {"name": "Updated", "is_active": False}
        serializer = ReportScheduleUpdateSerializer(schedule, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")
        self.assertFalse(updated.is_active)

    def test_display_serializer(self):
        schedule = ReportSchedule.objects.create(name="Display", cron_expression="0 12 * * *")
        serializer = ReportScheduleDisplaySerializer(schedule)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["cron_expression"], "0 12 * * *")