from django.test import TestCase
from students.models import Student, Guardian
from students.services.guardian import GuardianService
from students.serializers.guardian import (
    GuardianCreateSerializer,
    GuardianUpdateSerializer,
    GuardianDisplaySerializer,
)
from common.enums.parents import RelationshipType


class GuardianModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )

    def test_create_guardian(self):
        guardian = Guardian.objects.create(
            student=self.student,
            first_name="Maria",
            last_name="Dela Cruz",
            relationship=RelationshipType.MOTHER,
            contact_number="09123456789",
            is_primary=True
        )
        self.assertEqual(guardian.student, self.student)
        self.assertEqual(guardian.first_name, "Maria")
        self.assertTrue(guardian.is_primary)

    def test_str_method(self):
        guardian = Guardian.objects.create(student=self.student, first_name="Pedro", last_name="Santos", relationship=RelationshipType.FATHER)
        expected = f"Santos, Pedro - {self.student}"
        self.assertEqual(str(guardian), expected)


class GuardianServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )

    def test_create_guardian(self):
        guardian = GuardianService.create_guardian(
            student=self.student,
            first_name="Jose",
            last_name="Santos",
            relationship=RelationshipType.FATHER,
            contact_number="09987654321",
            is_primary=True
        )
        self.assertEqual(guardian.student, self.student)
        self.assertTrue(guardian.is_primary)

    def test_ensure_single_primary(self):
        g1 = GuardianService.create_guardian(self.student, "Mother1", "A", RelationshipType.MOTHER, "111", is_primary=True)
        g2 = GuardianService.create_guardian(self.student, "Father1", "B", RelationshipType.FATHER, "222", is_primary=True)
        g1.refresh_from_db()
        self.assertFalse(g1.is_primary)
        self.assertTrue(g2.is_primary)

    def test_get_primary_guardian(self):
        Guardian.objects.create(student=self.student, first_name="NotPrimary", last_name="X", relationship=RelationshipType.MOTHER, is_primary=False)
        primary = Guardian.objects.create(student=self.student, first_name="Primary", last_name="Y", relationship=RelationshipType.FATHER, is_primary=True)
        fetched = GuardianService.get_primary_guardian(self.student.id)
        self.assertEqual(fetched, primary)


class GuardianSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "first_name": "Juana",
            "last_name": "Penduko",
            "relationship": RelationshipType.MOTHER,
            "contact_number": "09123456789",
            "is_primary": True
        }
        serializer = GuardianCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        guardian = serializer.save()
        self.assertEqual(guardian.student, self.student)

    def test_update_serializer(self):
        guardian = Guardian.objects.create(student=self.student, first_name="Old", last_name="Name", relationship=RelationshipType.FATHER, contact_number="111")
        data = {"first_name": "New", "is_primary": True}
        serializer = GuardianUpdateSerializer(guardian, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.first_name, "New")
        self.assertTrue(updated.is_primary)

    def test_display_serializer(self):
        guardian = Guardian.objects.create(student=self.student, first_name="Display", last_name="Test", relationship=RelationshipType.MOTHER, contact_number="123")
        serializer = GuardianDisplaySerializer(guardian)
        self.assertEqual(serializer.data["first_name"], "Display")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)