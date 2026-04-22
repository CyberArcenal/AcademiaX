from django.test import TestCase
from datetime import date
from users.models import User
from teachers.models import Teacher, Specialization
from academic.models import Subject
from teachers.services.specialization import SpecializationService
from teachers.serializers.specialization import (
    SpecializationCreateSerializer,
    SpecializationUpdateSerializer,
    SpecializationDisplaySerializer,
)


class SpecializationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher", email="t@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1)
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")

    def test_create_specialization(self):
        spec = Specialization.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            is_primary=True,
            proficiency_level="EXPERT"
        )
        self.assertEqual(spec.teacher, self.teacher)
        self.assertEqual(spec.subject, self.subject)
        self.assertTrue(spec.is_primary)

    def test_str_method(self):
        spec = Specialization.objects.create(teacher=self.teacher, subject=self.subject)
        expected = f"{self.teacher} specializes in {self.subject.code}"
        self.assertEqual(str(spec), expected)


class SpecializationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Jane", last_name="Smith",
            birth_date=date(1985,1,1), gender="F", hire_date=date(2019,1,1)
        )
        self.subject1 = Subject.objects.create(code="SCI101", name="Biology")
        self.subject2 = Subject.objects.create(code="SCI102", name="Chemistry")

    def test_create_specialization(self):
        spec = SpecializationService.create_specialization(
            teacher=self.teacher,
            subject=self.subject1,
            is_primary=True,
            proficiency_level="ADVANCED"
        )
        self.assertEqual(spec.teacher, self.teacher)

    def test_set_primary_unset_previous(self):
        spec1 = SpecializationService.create_specialization(self.teacher, self.subject1, is_primary=True)
        spec2 = SpecializationService.create_specialization(self.teacher, self.subject2, is_primary=True)
        spec1.refresh_from_db()
        self.assertFalse(spec1.is_primary)
        self.assertTrue(spec2.is_primary)

    def test_get_primary_specialization(self):
        Specialization.objects.create(teacher=self.teacher, subject=self.subject1, is_primary=False)
        primary = Specialization.objects.create(teacher=self.teacher, subject=self.subject2, is_primary=True)
        fetched = SpecializationService.get_primary_specialization(self.teacher.id)
        self.assertEqual(fetched, primary)


class SpecializationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Mark", last_name="Brown",
            birth_date=date(1975,1,1), gender="M", hire_date=date(2015,1,1)
        )
        self.subject = Subject.objects.create(code="ENG101", name="English")

    def test_create_serializer_valid(self):
        data = {
            "teacher_id": self.teacher.id,
            "subject_id": self.subject.id,
            "is_primary": True,
            "proficiency_level": "INTERMEDIATE"
        }
        serializer = SpecializationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        spec = serializer.save()
        self.assertEqual(spec.teacher, self.teacher)

    def test_update_serializer(self):
        spec = Specialization.objects.create(teacher=self.teacher, subject=self.subject, is_primary=False)
        data = {"is_primary": True, "proficiency_level": "EXPERT"}
        serializer = SpecializationUpdateSerializer(spec, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_primary)

    def test_display_serializer(self):
        spec = Specialization.objects.create(teacher=self.teacher, subject=self.subject)
        serializer = SpecializationDisplaySerializer(spec)
        self.assertEqual(serializer.data["teacher"]["id"], self.teacher.id)
        self.assertEqual(serializer.data["subject"]["id"], self.subject.id)