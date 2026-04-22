from django.test import TestCase
from django.contrib.auth import get_user_model
from students.models import Student
from alumni.models import Alumni
from alumni.services.alumni import AlumniService
from alumni.serializers.alumni import (
    AlumniCreateSerializer,
    AlumniUpdateSerializer,
    AlumniDisplaySerializer,
)

User = get_user_model()


class AlumniModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alumni_user",
            email="alumni@example.com",
            password="testpass123"
        )
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2000-01-01",
            gender="M"
        )

    def test_create_alumni_with_student(self):
        alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025,
            batch="Batch 2025"
        )
        self.assertEqual(alumni.student, self.student)
        self.assertEqual(alumni.graduation_year, 2025)
        self.assertEqual(alumni.batch, "Batch 2025")
        self.assertTrue(alumni.is_active)

    def test_create_alumni_with_user(self):
        alumni = Alumni.objects.create(
            user=self.user,
            graduation_year=2025
        )
        self.assertEqual(alumni.user, self.user)

    def test_str_method_with_student(self):
        alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )
        expected = f"{self.student.get_full_name()} - 2025"
        self.assertEqual(str(alumni), expected)

    def test_str_method_with_user(self):
        alumni = Alumni.objects.create(
            user=self.user,
            graduation_year=2025
        )
        expected = f"{self.user.get_full_name()} - 2025"
        self.assertEqual(str(alumni), expected)


class AlumniServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alumni_svc",
            email="svc@example.com",
            password="test"
        )
        self.student = Student.objects.create(
            first_name="Maria",
            last_name="Santos",
            birth_date="2001-02-02",
            gender="F"
        )

    def test_create_alumni(self):
        alumni = AlumniService.create_alumni(
            graduation_year=2025,
            student=self.student,
            batch="Test Batch"
        )
        self.assertEqual(alumni.student, self.student)
        self.assertEqual(alumni.graduation_year, 2025)

    def test_get_alumni_by_id(self):
        created = Alumni.objects.create(student=self.student, graduation_year=2025)
        fetched = AlumniService.get_alumni_by_id(created.id)
        self.assertEqual(fetched, created)

    def test_get_alumni_by_student(self):
        created = Alumni.objects.create(student=self.student, graduation_year=2025)
        fetched = AlumniService.get_alumni_by_student(self.student.id)
        self.assertEqual(fetched, created)

    def test_update_alumni(self):
        alumni = Alumni.objects.create(student=self.student, graduation_year=2025)
        updated = AlumniService.update_alumni(alumni, {"graduation_year": 2026, "current_city": "Manila"})
        self.assertEqual(updated.graduation_year, 2026)
        self.assertEqual(updated.current_city, "Manila")

    def test_delete_alumni_soft(self):
        alumni = Alumni.objects.create(student=self.student, graduation_year=2025)
        AlumniService.delete_alumni(alumni, soft_delete=True)
        alumni.refresh_from_db()
        self.assertFalse(alumni.is_active)

    def test_search_alumni(self):
        Alumni.objects.create(student=self.student, graduation_year=2025)
        results = AlumniService.search_alumni("Maria")
        self.assertEqual(results.count(), 1)


class AlumniSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ser_user",
            email="ser@example.com",
            password="test"
        )
        self.student = Student.objects.create(
            first_name="Pedro",
            last_name="Penduko",
            birth_date="2002-03-03",
            gender="M"
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "graduation_year": 2025,
            "batch": "Batch 2025"
        }
        serializer = AlumniCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        alumni = serializer.save()
        self.assertEqual(alumni.student, self.student)

    def test_update_serializer(self):
        alumni = Alumni.objects.create(student=self.student, graduation_year=2025)
        data = {"graduation_year": 2026, "current_city": "Cebu"}
        serializer = AlumniUpdateSerializer(alumni, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.graduation_year, 2026)

    def test_display_serializer(self):
        alumni = Alumni.objects.create(student=self.student, graduation_year=2025)
        serializer = AlumniDisplaySerializer(alumni)
        self.assertEqual(serializer.data["graduation_year"], 2025)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)