from django.test import TestCase
from users.models import User
from reports.models import ReportTemplate
from reports.services.report_template import ReportTemplateService
from reports.serializers.report_template import (
    ReportTemplateCreateSerializer,
    ReportTemplateUpdateSerializer,
    ReportTemplateDisplaySerializer,
)
from common.enums.reports import ReportType


class ReportTemplateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_template(self):
        template = ReportTemplate.objects.create(
            name="Report Card Template",
            report_type=ReportType.REPORT_CARD,
            template_file="templates/report_card.html",
            description="Standard report card",
            is_default=True,
            is_active=True,
            created_by=self.user
        )
        self.assertEqual(template.name, "Report Card Template")
        self.assertTrue(template.is_default)

    def test_str_method(self):
        template = ReportTemplate.objects.create(name="Test", report_type=ReportType.TRANSCRIPT)
        self.assertEqual(str(template), "Test (Transcript)")


class ReportTemplateServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")

    def test_create_template(self):
        template = ReportTemplateService.create_template(
            name="Attendance Template",
            report_type=ReportType.ATTENDANCE_SUMMARY,
            template_file="templates/attendance.html",
            description="Attendance summary",
            is_default=False,
            created_by=self.user
        )
        self.assertEqual(template.name, "Attendance Template")

    def test_get_default_template(self):
        ReportTemplate.objects.create(name="Default", report_type=ReportType.REPORT_CARD, is_default=True, template_file="a.html")
        fetched = ReportTemplateService.get_default_template(ReportType.REPORT_CARD)
        self.assertEqual(fetched.name, "Default")

    def test_set_as_default(self):
        t1 = ReportTemplate.objects.create(name="T1", report_type=ReportType.CUSTOM, is_default=False, template_file="a.html")
        t2 = ReportTemplate.objects.create(name="T2", report_type=ReportType.CUSTOM, is_default=True, template_file="b.html")
        updated = ReportTemplateService.set_as_default(t1)
        t2.refresh_from_db()
        self.assertTrue(updated.is_default)
        self.assertFalse(t2.is_default)


class ReportTemplateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", email="admin3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "name": "Grade Sheet Template",
            "report_type": ReportType.GRADE_SHEET,
            "template_file": "templates/gradesheet.html",
            "description": "Grade sheet layout",
            "is_default": True,
            "created_by_id": self.user.id
        }
        serializer = ReportTemplateCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        template = serializer.save()
        self.assertEqual(template.name, "Grade Sheet Template")

    def test_update_serializer(self):
        template = ReportTemplate.objects.create(name="Old", report_type=ReportType.CUSTOM, is_default=False, template_file="old.html")
        data = {"name": "Updated", "is_default": True}
        serializer = ReportTemplateUpdateSerializer(template, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")
        self.assertTrue(updated.is_default)

    def test_display_serializer(self):
        template = ReportTemplate.objects.create(name="Display", report_type=ReportType.REPORT_CARD, template_file="disp.html")
        serializer = ReportTemplateDisplaySerializer(template)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["report_type"], ReportType.REPORT_CARD)