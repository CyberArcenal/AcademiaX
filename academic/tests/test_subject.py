from django.test import TestCase
from django.core.exceptions import ValidationError
from academic.models import Subject
from academic.services.subject import SubjectService
from academic.serializers.subject import SubjectCreateSerializer, SubjectUpdateSerializer, SubjectDisplaySerializer
from common.enums.academic import SubjectType


class SubjectModelTest(TestCase):
    def test_create_subject_minimal(self):
        subject = Subject.objects.create(
            code="MATH101",
            name="Algebra",
            units=3.0,
            subject_type=SubjectType.CORE
        )
        self.assertEqual(subject.code, "MATH101")
        self.assertEqual(subject.name, "Algebra")
        self.assertEqual(subject.units, 3.0)
        self.assertTrue(subject.is_active)

    def test_code_uppercase_auto(self):
        subject = Subject.objects.create(
            code="math101",
            name="Algebra"
        )
        self.assertEqual(subject.code, "MATH101")

    def test_name_title_auto(self):
        subject = Subject.objects.create(
            code="MATH101",
            name="algebra"
        )
        self.assertEqual(subject.name, "Algebra")

    def test_unique_code_constraint(self):
        Subject.objects.create(code="MATH101", name="Algebra")
        with self.assertRaises(Exception):
            Subject.objects.create(code="MATH101", name="Geometry")

    def test_str_method(self):
        subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.assertEqual(str(subject), "MATH101 - Algebra")


class SubjectServiceTest(TestCase):
    def test_create_subject(self):
        subject = SubjectService.create_subject(
            code="SCI101",
            name="Biology",
            units=4.0,
            subject_type=SubjectType.CORE
        )
        self.assertEqual(subject.code, "SCI101")
        self.assertEqual(subject.name, "Biology")
        self.assertEqual(subject.units, 4.0)

    def test_get_subject_by_id(self):
        created = Subject.objects.create(code="PHY101", name="Physics")
        fetched = SubjectService.get_subject_by_id(created.id)
        self.assertEqual(fetched, created)

    def test_get_subject_by_code(self):
        created = Subject.objects.create(code="CHEM101", name="Chemistry")
        fetched = SubjectService.get_subject_by_code("chem101")
        self.assertEqual(fetched, created)

    def test_update_subject(self):
        subject = Subject.objects.create(code="ENG101", name="English")
        updated = SubjectService.update_subject(subject, {"name": "Advanced English", "units": 2.0})
        self.assertEqual(updated.name, "Advanced English")
        self.assertEqual(updated.units, 2.0)

    def test_delete_subject_soft(self):
        subject = Subject.objects.create(code="HIST101", name="History")
        SubjectService.delete_subject(subject, soft_delete=True)
        subject.refresh_from_db()
        self.assertFalse(subject.is_active)

    def test_delete_subject_hard(self):
        subject = Subject.objects.create(code="GEO101", name="Geography")
        SubjectService.delete_subject(subject, soft_delete=False)
        with self.assertRaises(Subject.DoesNotExist):
            Subject.objects.get(id=subject.id)

    def test_search_subjects(self):
        Subject.objects.create(code="MATH101", name="Algebra")
        Subject.objects.create(code="MATH102", name="Geometry")
        Subject.objects.create(code="SCI101", name="Biology")
        results = SubjectService.search_subjects("MATH")
        self.assertEqual(results.count(), 2)


class SubjectSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "code": "CS101",
            "name": "Computer Science",
            "units": 3.0,
            "subject_type": SubjectType.CORE
        }
        serializer = SubjectCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        subject = serializer.save()
        self.assertEqual(subject.code, "CS101")

    def test_create_serializer_invalid_missing_code(self):
        data = {"name": "No Code"}
        serializer = SubjectCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_update_serializer(self):
        subject = Subject.objects.create(code="ART101", name="Art")
        data = {"name": "Fine Arts", "units": 2.0}
        serializer = SubjectUpdateSerializer(subject, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Fine Arts")

    def test_display_serializer(self):
        subject = Subject.objects.create(code="MUSIC101", name="Music")
        serializer = SubjectDisplaySerializer(subject)
        self.assertEqual(serializer.data["code"], "MUSIC101")
        self.assertEqual(serializer.data["name"], "Music")