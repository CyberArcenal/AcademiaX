from django.test import TestCase
from datetime import date, time
from students.models import Student
from teachers.models import Teacher
from classes.models import Section, AcademicYear, GradeLevel
from academic.models import Subject
from attendance.models import StudentAttendance
from attendance.services.student_attendance import StudentAttendanceService
from attendance.serializers.student_attendance import (
    StudentAttendanceCreateSerializer,
    StudentAttendanceUpdateSerializer,
    StudentAttendanceDisplaySerializer,
)
from common.enums.attendance import AttendanceStatus, LateReason


class StudentAttendanceModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2010-01-01",
            gender="M"
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31)
        )
        self.section = Section.objects.create(
            name="A",
            grade_level=self.grade_level,
            academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")

    def test_create_attendance(self):
        attendance = StudentAttendance.objects.create(
            student=self.student,
            section=self.section,
            subject=self.subject,
            academic_year=self.academic_year,
            date=date(2025, 6, 10),
            status=AttendanceStatus.PRESENT,
            time_in=time(8, 0)
        )
        self.assertEqual(attendance.student, self.student)
        self.assertEqual(attendance.status, AttendanceStatus.PRESENT)

    def test_str_method(self):
        attendance = StudentAttendance.objects.create(
            student=self.student,
            section=self.section,
            subject=self.subject,
            academic_year=self.academic_year,
            date=date(2025, 6, 10),
            status=AttendanceStatus.PRESENT
        )
        expected = f"{self.student} - {self.subject.code} - 2025-06-10 - Present"
        self.assertEqual(str(attendance), expected)


class StudentAttendanceServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F")
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.section = Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="SCI101", name="Biology")

    def test_create_attendance(self):
        attendance = StudentAttendanceService.create_attendance(
            student=self.student,
            section=self.section,
            subject=self.subject,
            academic_year=self.academic_year,
            date=date(2025, 6, 15),
            status=AttendanceStatus.LATE,
            late_minutes=10,
            late_reason=LateReason.TRAFFIC
        )
        self.assertEqual(attendance.status, AttendanceStatus.LATE)
        self.assertEqual(attendance.late_minutes, 10)

    def test_get_attendance_by_student_date(self):
        StudentAttendance.objects.create(
            student=self.student, section=self.section, subject=self.subject,
            academic_year=self.academic_year, date=date(2025, 6, 15), status=AttendanceStatus.PRESENT
        )
        attendance = StudentAttendanceService.get_attendance_by_student_date(
            self.student.id, date(2025, 6, 15), self.subject.id, self.section.id
        )
        self.assertIsNotNone(attendance)

    def test_bulk_create_attendance(self):
        data = [
            {"student_id": self.student.id, "section_id": self.section.id, "subject_id": self.subject.id,
             "academic_year_id": self.academic_year.id, "date": date(2025, 6, 20), "status": AttendanceStatus.PRESENT},
        ]
        created = StudentAttendanceService.bulk_create_attendance(data)
        self.assertEqual(len(created), 1)


class StudentAttendanceSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M")
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="ENG101", name="English")

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "section_id": self.section.id,
            "subject_id": self.subject.id,
            "academic_year_id": self.academic_year.id,
            "date": "2025-06-25",
            "status": AttendanceStatus.ABSENT
        }
        serializer = StudentAttendanceCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        attendance = serializer.save()
        self.assertEqual(attendance.student, self.student)

    def test_update_serializer(self):
        attendance = StudentAttendance.objects.create(
            student=self.student, section=self.section, subject=self.subject,
            academic_year=self.academic_year, date=date(2025, 6, 25), status=AttendanceStatus.PRESENT
        )
        data = {"status": AttendanceStatus.ABSENT, "remarks": "Sick"}
        serializer = StudentAttendanceUpdateSerializer(attendance, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, AttendanceStatus.ABSENT)

    def test_display_serializer(self):
        attendance = StudentAttendance.objects.create(
            student=self.student, section=self.section, subject=self.subject,
            academic_year=self.academic_year, date=date(2025, 6, 25), status=AttendanceStatus.PRESENT
        )
        serializer = StudentAttendanceDisplaySerializer(attendance)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)
        self.assertEqual(serializer.data["status"], AttendanceStatus.PRESENT)