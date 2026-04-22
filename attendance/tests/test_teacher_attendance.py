from django.test import TestCase
from datetime import date, time
from users.models import User
from teachers.models import Teacher
from hr.models import Employee  # if needed for recorded_by
from attendance.models import TeacherAttendance
from attendance.services.teacher_attendance import TeacherAttendanceService
from attendance.serializers.teacher_attendance import (
    TeacherAttendanceCreateSerializer,
    TeacherAttendanceUpdateSerializer,
    TeacherAttendanceDisplaySerializer,
)
from common.enums.attendance import AttendanceStatus


class TeacherAttendanceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher1", email="t1@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            birth_date="1980-01-01",
            gender="M",
            hire_date="2020-01-01"
        )

    def test_create_teacher_attendance(self):
        attendance = TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date(2025, 6, 10),
            status=AttendanceStatus.PRESENT,
            time_in=time(8, 0),
            time_out=time(17, 0)
        )
        self.assertEqual(attendance.teacher, self.teacher)
        self.assertEqual(attendance.status, AttendanceStatus.PRESENT)

    def test_str_method(self):
        attendance = TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date(2025, 6, 10),
            status=AttendanceStatus.PRESENT
        )
        expected = f"{self.teacher} - 2025-06-10 - Present"
        self.assertEqual(str(attendance), expected)


class TeacherAttendanceServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            birth_date="1985-01-01",
            gender="F",
            hire_date="2019-01-01"
        )

    def test_create_attendance(self):
        attendance = TeacherAttendanceService.create_attendance(
            teacher=self.teacher,
            date=date(2025, 6, 15),
            status=AttendanceStatus.LATE,
            late_minutes=15
        )
        self.assertEqual(attendance.teacher, self.teacher)
        self.assertEqual(attendance.status, AttendanceStatus.LATE)

    def test_get_attendance_by_teacher_date(self):
        TeacherAttendance.objects.create(teacher=self.teacher, date=date(2025, 6, 15), status=AttendanceStatus.PRESENT)
        attendance = TeacherAttendanceService.get_attendance_by_teacher_date(self.teacher.id, date(2025, 6, 15))
        self.assertIsNotNone(attendance)


class TeacherAttendanceSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Mark",
            last_name="Brown",
            birth_date="1975-01-01",
            gender="M",
            hire_date="2015-01-01"
        )

    def test_create_serializer_valid(self):
        data = {
            "teacher_id": self.teacher.id,
            "date": "2025-06-20",
            "status": AttendanceStatus.ABSENT
        }
        serializer = TeacherAttendanceCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        attendance = serializer.save()
        self.assertEqual(attendance.teacher, self.teacher)

    def test_update_serializer(self):
        attendance = TeacherAttendance.objects.create(teacher=self.teacher, date=date(2025, 6, 20), status=AttendanceStatus.PRESENT)
        data = {"status": AttendanceStatus.ABSENT, "remarks": "Sick"}
        serializer = TeacherAttendanceUpdateSerializer(attendance, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, AttendanceStatus.ABSENT)

    def test_display_serializer(self):
        attendance = TeacherAttendance.objects.create(teacher=self.teacher, date=date(2025, 6, 20), status=AttendanceStatus.PRESENT)
        serializer = TeacherAttendanceDisplaySerializer(attendance)
        self.assertEqual(serializer.data["teacher"]["id"], self.teacher.id)
        self.assertEqual(serializer.data["status"], AttendanceStatus.PRESENT)