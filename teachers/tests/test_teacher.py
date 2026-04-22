from django.test import TestCase
from datetime import date
from users.models import User
from teachers.models import Teacher
from teachers.services.teacher import TeacherService
from teachers.serializers.teacher import (
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    TeacherDisplaySerializer,
)
from common.enums.teachers import TeacherStatus, TeacherType


class TeacherModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher1", email="t1@example.com", password="test")

    def test_create_teacher(self):
        teacher = Teacher.objects.create(
            user=self.user,
            teacher_id="TCH-2025-000001",
            first_name="John",
            last_name="Doe",
            birth_date=date(1980, 1, 1),
            gender="M",
            hire_date=date(2020, 6, 1),
            teacher_type=TeacherType.FULL_TIME,
            status=TeacherStatus.ACTIVE
        )
        self.assertEqual(teacher.user, self.user)
        self.assertEqual(teacher.first_name, "John")

    def test_get_full_name(self):
        teacher = Teacher.objects.create(first_name="Maria", middle_name="Santos", last_name="Cruz", suffix="Jr.")
        self.assertEqual(teacher.get_full_name(), "Maria Santos Cruz Jr.")

    def test_str_method(self):
        teacher = Teacher.objects.create(teacher_id="TCH-001", first_name="Pedro", last_name="Penduko")
        self.assertEqual(str(teacher), "TCH-001 - Penduko, Pedro")


class TeacherServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")

    def test_generate_teacher_id(self):
        tid = TeacherService.generate_teacher_id()
        self.assertTrue(tid.startswith(f"TCH-{date.today().year}"))

    def test_create_teacher(self):
        teacher = TeacherService.create_teacher(
            user=self.user,
            first_name="Jose",
            last_name="Rizal",
            birth_date=date(1861, 6, 19),
            gender="M",
            hire_date=date(1890, 1, 1),
            teacher_type=TeacherType.PART_TIME
        )
        self.assertIsNotNone(teacher.teacher_id)
        self.assertEqual(teacher.status, TeacherStatus.ACTIVE)

    def test_get_teacher_by_user(self):
        created = Teacher.objects.create(
            user=self.user, first_name="Test", last_name="User",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1)
        )
        fetched = TeacherService.get_teacher_by_user(self.user.id)
        self.assertEqual(fetched, created)

    def test_update_status(self):
        teacher = Teacher.objects.create(
            user=self.user, first_name="ToUpdate", last_name="Status",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1),
            status=TeacherStatus.ACTIVE
        )
        updated = TeacherService.update_status(teacher, TeacherStatus.ON_LEAVE)
        self.assertEqual(updated.status, TeacherStatus.ON_LEAVE)


class TeacherSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "user_id": self.user.id,
            "first_name": "Andres",
            "last_name": "Bonifacio",
            "birth_date": "1863-11-30",
            "gender": "M",
            "hire_date": "1892-01-01",
            "teacher_type": TeacherType.FULL_TIME
        }
        serializer = TeacherCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        teacher = serializer.save()
        self.assertEqual(teacher.user, self.user)

    def test_update_serializer(self):
        teacher = Teacher.objects.create(
            user=self.user, first_name="Old", last_name="Name",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1)
        )
        data = {"first_name": "New", "contact_number": "09123456789"}
        serializer = TeacherUpdateSerializer(teacher, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.first_name, "New")

    def test_display_serializer(self):
        teacher = Teacher.objects.create(
            user=self.user, first_name="Display", last_name="Test",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1)
        )
        serializer = TeacherDisplaySerializer(teacher)
        self.assertEqual(serializer.data["first_name"], "Display")
        self.assertEqual(serializer.data["user"]["id"], self.user.id)