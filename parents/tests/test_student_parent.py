from django.test import TestCase
from users.models import User
from students.models import Student
from parents.models import Parent, StudentParent
from parents.services.student_parent import StudentParentService
from parents.serializers.student_parent import (
    StudentParentCreateSerializer,
    StudentParentUpdateSerializer,
    StudentParentDisplaySerializer,
)
from common.enums.parents import RelationshipType


class StudentParentModelTest(TestCase):
    def setUp(self):
        self.user_parent = User.objects.create_user(username="parent1", email="p1@example.com", password="test")
        self.parent = Parent.objects.create(user=self.user_parent)
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )

    def test_create_relationship(self):
        rel = StudentParent.objects.create(
            student=self.student,
            parent=self.parent,
            relationship=RelationshipType.FATHER,
            is_primary_contact=True,
            can_pickup=True
        )
        self.assertEqual(rel.student, self.student)
        self.assertEqual(rel.parent, self.parent)
        self.assertTrue(rel.is_primary_contact)

    def test_str_method(self):
        rel = StudentParent.objects.create(student=self.student, parent=self.parent, relationship=RelationshipType.MOTHER)
        expected = f"{self.parent} - {self.student} (Mother)"
        self.assertEqual(str(rel), expected)


class StudentParentServiceTest(TestCase):
    def setUp(self):
        self.user_parent = User.objects.create_user(username="parent2", email="p2@example.com", password="test")
        self.parent = Parent.objects.create(user=self.user_parent)
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.student2 = Student.objects.create(
            first_name="Jose", last_name="Santos", birth_date="2008-05-05", gender="M"
        )

    def test_create_relationship(self):
        rel = StudentParentService.create_relationship(
            student=self.student,
            parent=self.parent,
            relationship=RelationshipType.GUARDIAN,
            is_primary_contact=True
        )
        self.assertEqual(rel.student, self.student)

    def test_ensure_single_primary(self):
        rel1 = StudentParentService.create_relationship(self.student, self.parent, RelationshipType.FATHER, is_primary_contact=True)
        rel2 = StudentParentService.create_relationship(self.student, self.parent, RelationshipType.MOTHER, is_primary_contact=True)
        rel1.refresh_from_db()
        self.assertFalse(rel1.is_primary_contact)
        self.assertTrue(rel2.is_primary_contact)

    def test_get_primary_contact(self):
        StudentParent.objects.create(student=self.student, parent=self.parent, relationship=RelationshipType.FATHER, is_primary_contact=False)
        primary = StudentParent.objects.create(student=self.student, parent=self.parent, relationship=RelationshipType.MOTHER, is_primary_contact=True)
        fetched = StudentParentService.get_primary_contact(self.student.id)
        self.assertEqual(fetched, primary)


class StudentParentSerializerTest(TestCase):
    def setUp(self):
        self.user_parent = User.objects.create_user(username="parent3", email="p3@example.com", password="test")
        self.parent = Parent.objects.create(user=self.user_parent)
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "parent_id": self.parent.id,
            "relationship": RelationshipType.FATHER,
            "is_primary_contact": True
        }
        serializer = StudentParentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        rel = serializer.save()
        self.assertEqual(rel.student, self.student)

    def test_update_serializer(self):
        rel = StudentParent.objects.create(student=self.student, parent=self.parent, relationship=RelationshipType.FATHER)
        data = {"is_primary_contact": True, "receives_academic_updates": False}
        serializer = StudentParentUpdateSerializer(rel, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_primary_contact)
        self.assertFalse(updated.receives_academic_updates)

    def test_display_serializer(self):
        rel = StudentParent.objects.create(student=self.student, parent=self.parent, relationship=RelationshipType.MOTHER)
        serializer = StudentParentDisplaySerializer(rel)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)
        self.assertEqual(serializer.data["parent"]["id"], self.parent.id)