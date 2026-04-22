from django.test import TestCase
from datetime import date
from decimal import Decimal
from academic.models.subject import Subject
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from attendance.models import StudentAttendanceSummary, StudentAttendance
from attendance.services.attendance_summary import StudentAttendanceSummaryService
from attendance.serializers.attendance_summary import (
    StudentAttendanceSummaryCreateSerializer,
    StudentAttendanceSummaryUpdateSerializer,
    StudentAttendanceSummaryDisplaySerializer,
)
from common.enums.attendance import AttendanceStatus


class StudentAttendanceSummaryModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2010-01-01",
            gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31)
        )

    def test_create_summary(self):
        summary = StudentAttendanceSummary.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            term="First Quarter",
            total_present=20,
            total_absent=2,
            total_late=1,
            attendance_rate=Decimal('86.96')
        )
        self.assertEqual(summary.student, self.student)
        self.assertEqual(summary.total_present, 20)
        self.assertEqual(summary.attendance_rate, Decimal('86.96'))

    def test_str_method(self):
        summary = StudentAttendanceSummary.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            term="First Quarter"
        )
        expected = f"{self.student} - {self.academic_year} - First Quarter"
        self.assertEqual(str(summary), expected)


class StudentAttendanceSummaryServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="A", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")

    def test_create_or_update_summary(self):
        summary = StudentAttendanceSummaryService.create_or_update_summary(
            student=self.student,
            academic_year=self.academic_year,
            term="First Quarter",
            total_present=15,
            total_absent=1
        )
        self.assertEqual(summary.student, self.student)
        self.assertEqual(summary.total_present, 15)

    def test_get_summary_by_student_term(self):
        StudentAttendanceSummary.objects.create(
            student=self.student, academic_year=self.academic_year, term="First Quarter", total_present=10
        )
        summary = StudentAttendanceSummaryService.get_summary_by_student_term(
            self.student.id, self.academic_year.id, "First Quarter"
        )
        self.assertIsNotNone(summary)

    def test_update_summary_from_attendance(self):
        # Create some attendance records
        StudentAttendance.objects.create(
            student=self.student, section=self.section, subject=self.subject,
            academic_year=self.academic_year, date=date(2025, 6, 1), status=AttendanceStatus.PRESENT
        )
        StudentAttendance.objects.create(
            student=self.student, section=self.section, subject=self.subject,
            academic_year=self.academic_year, date=date(2025, 6, 2), status=AttendanceStatus.ABSENT
        )
        StudentAttendance.objects.create(
            student=self.student, section=self.section, subject=self.subject,
            academic_year=self.academic_year, date=date(2025, 6, 3), status=AttendanceStatus.LATE
        )
        summary = StudentAttendanceSummaryService.update_summary_from_attendance(
            student_id=self.student.id,
            academic_year_id=self.academic_year.id,
            term="First Week",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3)
        )
        self.assertEqual(summary.total_present, 1)
        self.assertEqual(summary.total_absent, 1)
        self.assertEqual(summary.total_late, 1)


class StudentAttendanceSummarySerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "academic_year_id": self.academic_year.id,
            "term": "Second Quarter",
            "total_present": 18,
            "total_absent": 2
        }
        serializer = StudentAttendanceSummaryCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        summary = serializer.save()
        self.assertEqual(summary.student, self.student)

    def test_update_serializer(self):
        summary = StudentAttendanceSummary.objects.create(
            student=self.student, academic_year=self.academic_year, term="Third Quarter", total_present=10
        )
        data = {"total_present": 15, "attendance_rate": "83.33"}
        serializer = StudentAttendanceSummaryUpdateSerializer(summary, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.total_present, 15)

    def test_display_serializer(self):
        summary = StudentAttendanceSummary.objects.create(
            student=self.student, academic_year=self.academic_year, term="Fourth Quarter", total_present=20
        )
        serializer = StudentAttendanceSummaryDisplaySerializer(summary)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)
        self.assertEqual(serializer.data["term"], "Fourth Quarter")