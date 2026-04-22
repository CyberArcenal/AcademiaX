from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User
from reports.models import Report
from reports.services.report import ReportService
from reports.serializers.report import (
    ReportCreateSerializer,
    ReportUpdateSerializer,
    ReportDisplaySerializer,
)
from common.enums.reports import ReportType, ReportFormat, ReportStatus


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_report(self):
        report = Report.objects.create(
            name="Student List",
            report_type=ReportType.CUSTOM,
            format=ReportFormat.PDF,
            parameters={"grade_level": "G7"},
            status=ReportStatus.PENDING,
            generated_by=self.user
        )
        self.assertEqual(report.name, "Student List")
        self.assertEqual(report.status, ReportStatus.PENDING)

    def test_str_method(self):
        report = Report.objects.create(name="Test Report", report_type=ReportType.REPORT_CARD)
        self.assertEqual(str(report), f"Test Report - Report Card (None)")


class ReportServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")

    def test_create_report(self):
        report = ReportService.create_report(
            name="Attendance Summary",
            report_type=ReportType.ATTENDANCE_SUMMARY,
            format=ReportFormat.EXCEL,
            parameters={"month": "January"},
            generated_by=self.user
        )
        self.assertEqual(report.name, "Attendance Summary")

    def test_mark_completed(self):
        report = Report.objects.create(name="Pending", report_type=ReportType.CUSTOM, status=ReportStatus.PENDING)
        completed = ReportService.mark_completed(report, "http://example.com/report.pdf", 1024)
        self.assertEqual(completed.status, ReportStatus.COMPLETED)
        self.assertEqual(completed.file_url, "http://example.com/report.pdf")

    def test_get_reports_by_user(self):
        Report.objects.create(name="R1", generated_by=self.user)
        Report.objects.create(name="R2", generated_by=self.user)
        reports = ReportService.get_reports_by_user(self.user.id)
        self.assertEqual(reports.count(), 2)


class ReportSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", email="admin3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "name": "Enrollment Report",
            "report_type": ReportType.ENROLLMENT_REPORT,
            "format": ReportFormat.CSV,
            "parameters": {"academic_year": "2025-2026"},
            "generated_by_id": self.user.id
        }
        serializer = ReportCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        report = serializer.save()
        self.assertEqual(report.name, "Enrollment Report")

    def test_update_serializer(self):
        report = Report.objects.create(name="Old", report_type=ReportType.CUSTOM, status=ReportStatus.PENDING)
        data = {"status": ReportStatus.COMPLETED, "file_url": "http://example.com/file.pdf"}
        serializer = ReportUpdateSerializer(report, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, ReportStatus.COMPLETED)

    def test_display_serializer(self):
        report = Report.objects.create(name="Display", report_type=ReportType.REPORT_CARD)
        serializer = ReportDisplaySerializer(report)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["report_type"], ReportType.REPORT_CARD)