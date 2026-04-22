from django.test import TestCase
from django.core.exceptions import ValidationError
from academic.models import Subject, Prerequisite
from academic.services.prerequisite import PrerequisiteService
from academic.serializers.prerequisite import (
    PrerequisiteCreateSerializer,
    PrerequisiteUpdateSerializer,
    PrerequisiteDisplaySerializer,
)
from common.enums.academic import SubjectType


class PrerequisiteModelTest(TestCase):
    def setUp(self):
        self.subject_a = Subject.objects.create(
            code="MATH101",
            name="Algebra",
            units=3.0,
            subject_type=SubjectType.CORE
        )
        self.subject_b = Subject.objects.create(
            code="MATH201",
            name="Calculus",
            units=3.0,
            subject_type=SubjectType.CORE
        )

    def test_create_prerequisite(self):
        prereq = Prerequisite.objects.create(
            subject=self.subject_b,
            required_subject=self.subject_a,
            is_optional=False,
            notes="Must pass Algebra first"
        )
        self.assertEqual(prereq.subject, self.subject_b)
        self.assertEqual(prereq.required_subject, self.subject_a)
        self.assertFalse(prereq.is_optional)
        self.assertEqual(prereq.notes, "Must pass Algebra first")

    def test_unique_together(self):
        Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a)
        with self.assertRaises(Exception):
            Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a)

    def test_str_method(self):
        prereq = Prerequisite.objects.create(
            subject=self.subject_b,
            required_subject=self.subject_a
        )
        expected = f"{self.subject_b.code} requires {self.subject_a.code}"
        self.assertEqual(str(prereq), expected)


class PrerequisiteServiceTest(TestCase):
    def setUp(self):
        self.subject_a = Subject.objects.create(code="ENG101", name="English 1")
        self.subject_b = Subject.objects.create(code="ENG201", name="English 2")
        self.subject_c = Subject.objects.create(code="ENG301", name="English 3")

    def test_add_prerequisite(self):
        prereq = PrerequisiteService.add_prerequisite(
            subject=self.subject_b,
            required_subject=self.subject_a,
            is_optional=False,
            notes="Required"
        )
        self.assertEqual(prereq.subject, self.subject_b)
        self.assertEqual(prereq.required_subject, self.subject_a)

    def test_get_prerequisites_for_subject(self):
        Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a)
        Prerequisite.objects.create(subject=self.subject_c, required_subject=self.subject_b)
        prereqs = PrerequisiteService.get_prerequisites_for_subject(self.subject_c.id)
        self.assertEqual(prereqs.count(), 1)
        self.assertEqual(prereqs.first().required_subject, self.subject_b)

    def test_get_subjects_requiring(self):
        Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a)
        Prerequisite.objects.create(subject=self.subject_c, required_subject=self.subject_a)
        requiring = PrerequisiteService.get_subjects_requiring(self.subject_a.id)
        self.assertEqual(requiring.count(), 2)

    def test_remove_prerequisite(self):
        prereq = Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a)
        success = PrerequisiteService.remove_prerequisite(prereq)
        self.assertTrue(success)
        with self.assertRaises(Prerequisite.DoesNotExist):
            Prerequisite.objects.get(id=prereq.id)

    def test_update_prerequisite(self):
        prereq = Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a, is_optional=False)
        updated = PrerequisiteService.update_prerequisite(prereq, is_optional=True, notes="Now optional")
        self.assertTrue(updated.is_optional)
        self.assertEqual(updated.notes, "Now optional")

    def test_check_prerequisites(self):
        Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a, is_optional=False)
        Prerequisite.objects.create(subject=self.subject_c, required_subject=self.subject_b, is_optional=False)
        # Student completed subject_a only
        completed = [self.subject_a.id]
        meets_b = PrerequisiteService.check_prerequisites(self.subject_b, completed)
        meets_c = PrerequisiteService.check_prerequisites(self.subject_c, completed)
        self.assertTrue(meets_b)
        self.assertFalse(meets_c)
        # Student completed both subject_a and subject_b
        completed_all = [self.subject_a.id, self.subject_b.id]
        meets_c_all = PrerequisiteService.check_prerequisites(self.subject_c, completed_all)
        self.assertTrue(meets_c_all)


class PrerequisiteSerializerTest(TestCase):
    def setUp(self):
        self.subject_a = Subject.objects.create(code="SCI101", name="General Science")
        self.subject_b = Subject.objects.create(code="SCI201", name="Biology")

    def test_create_serializer_valid(self):
        data = {
            "subject_id": self.subject_b.id,
            "required_subject_id": self.subject_a.id,
            "is_optional": False,
            "notes": "Must pass General Science"
        }
        serializer = PrerequisiteCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        prereq = serializer.save()
        self.assertEqual(prereq.subject, self.subject_b)
        self.assertEqual(prereq.required_subject, self.subject_a)

    def test_create_serializer_invalid_missing_subject(self):
        data = {"required_subject_id": self.subject_a.id}
        serializer = PrerequisiteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("subject_id", serializer.errors)

    def test_update_serializer(self):
        prereq = Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a, is_optional=False)
        data = {"is_optional": True, "notes": "Updated notes"}
        serializer = PrerequisiteUpdateSerializer(prereq, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_optional)
        self.assertEqual(updated.notes, "Updated notes")

    def test_display_serializer(self):
        prereq = Prerequisite.objects.create(subject=self.subject_b, required_subject=self.subject_a)
        serializer = PrerequisiteDisplaySerializer(prereq)
        self.assertEqual(serializer.data["subject"]["id"], self.subject_b.id)
        self.assertEqual(serializer.data["required_subject"]["id"], self.subject_a.id)