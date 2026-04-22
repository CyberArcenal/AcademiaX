from django.test import TestCase
from users.models import User
from reports.models import Report, ReportLog
from reports.services.report_log import ReportLogService
from reports.serializers.report_log import (
    ReportLogCreateSerializer,
    ReportLogUpdateSerializer,
    ReportLogDisplaySerializer,
)
from common.enums.reports import ReportType, ReportFormat, ReportStatus


class ReportLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")
        self.report = Report.objects.create(
            name="Test Report",
            report_type=ReportType.CUSTOM,
            status=ReportStatus.COMPLETED,
            generated_by=self.user
        )

    def test_create_report_log(self):
        log = ReportLog.objects.create(
            report=self.report,
            action="GENERATED",
            performed_by=self.user,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            details={"duration": 2.5}
        )
        self.assertEqual(log.report, self.report)
        self.assertEqual(log.action, "GENERATED")

    def test_str_method(self):
        log = ReportLog.objects.create(report=self.report, action="DOWNLOADED")
        expected = f"{self.report.name} - DOWNLOADED by None"
        self.assertEqual(str(log), expected)


class ReportLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")
        self.report = Report.objects.create(
            name="Attendance Report",
            report_type=ReportType.ATTENDANCE_SUMMARY,
            generated_by=self.user
        )

    def test_create_log(self):
        log = ReportLogService.create_log(
            report=self.report,
            action="EMAILED",
            performed_by=self.user,
            ip_address="192.168.1.1",
            details={"recipient": "user@example.com"}
        )
        self.assertEqual(log.report, self.report)
        self.assertEqual(log.action, "EMAILED")

    def test_get_logs_by_report(self):
        ReportLog.objects.create(report=self.report, action="GENERATED")
        ReportLog.objects.create(report=self.report, action="DOWNLOADED")
        logs = ReportLogService.get_logs_by_report(self.report.id)
        self.assertEqual(logs.count(), 2)


class ReportLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", email="admin3@example.com", password="test")
        self.report = Report.objects.create(
            name="Grade Report",
            report_type=ReportType.GRADE_SHEET,
            generated_by=self.user
        )

    def test_create_serializer_valid(self):
        data = {
            "report_id": self.report.id,
            "action": "GENERATED",
            "performed_by_id": self.user.id,
            "ip_address": "10.0.0.1",
            "details": {"info": "test"}
        }
        serializer = ReportLogCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.report, self.report)

    def test_update_serializer(self):
        log = ReportLog.objects.create(report=self.report, action="GENERATED")
        # Logs are typically immutable, but update serializer exists
        data = {}  # No fields to update
        serializer = ReportLogUpdateSerializer(log, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.action, "GENERATED")  # unchanged

    def test_display_serializer(self):
        log = ReportLog.objects.create(report=self.report, action="DOWNLOADED", performed_by=self.user)
        serializer = ReportLogDisplaySerializer(log)
        self.assertEqual(serializer.data["action"], "DOWNLOADED")
        self.assertEqual(serializer.data["report"]["id"], self.report.id)