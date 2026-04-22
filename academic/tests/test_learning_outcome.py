from django.test import TestCase
from django.core.exceptions import ValidationError
from academic.models import Subject, LearningOutcome
from academic.services.learning_outcome import LearningOutcomeService
from academic.serializers.learning_outcome import (
    LearningOutcomeCreateSerializer,
    LearningOutcomeUpdateSerializer,
    LearningOutcomeDisplaySerializer,
)
from common.enums.academic import SubjectType


class LearningOutcomeModelTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(
            code="SCI101",
            name="Biology",
            units=3.0,
            subject_type=SubjectType.CORE
        )

    def test_create_learning_outcome(self):
        outcome = LearningOutcome.objects.create(
            subject=self.subject,
            code="LO1",
            description="Explain the cell theory",
            order=1
        )
        self.assertEqual(outcome.subject, self.subject)
        self.assertEqual(outcome.code, "LO1")
        self.assertEqual(outcome.description, "Explain the cell theory")
        self.assertEqual(outcome.order, 1)

    def test_code_uppercase_auto(self):
        outcome = LearningOutcome.objects.create(
            subject=self.subject,
            code="lo2",
            description="Describe cell structures",
            order=2
        )
        self.assertEqual(outcome.code, "LO2")

    def test_unique_together_subject_code(self):
        LearningOutcome.objects.create(subject=self.subject, code="LO1", description="First", order=1)
        with self.assertRaises(Exception):
            LearningOutcome.objects.create(subject=self.subject, code="LO1", description="Duplicate", order=2)

    def test_str_method(self):
        outcome = LearningOutcome.objects.create(
            subject=self.subject,
            code="LO1",
            description="Explain the cell theory",
            order=1
        )
        expected = f"{self.subject.code} - LO1: Explain the cell theory"
        self.assertEqual(str(outcome), expected)


class LearningOutcomeServiceTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(code="CHEM101", name="Chemistry")

    def test_create_outcome(self):
        outcome = LearningOutcomeService.create_outcome(
            subject=self.subject,
            code="LO1",
            description="Understand atomic structure",
            order=1
        )
        self.assertEqual(outcome.subject, self.subject)
        self.assertEqual(outcome.code, "LO1")
        self.assertEqual(outcome.description, "Understand atomic structure")

    def test_get_outcomes_by_subject(self):
        LearningOutcome.objects.create(subject=self.subject, code="LO1", description="First", order=1)
        LearningOutcome.objects.create(subject=self.subject, code="LO2", description="Second", order=2)
        outcomes = LearningOutcomeService.get_outcomes_by_subject(self.subject.id)
        self.assertEqual(outcomes.count(), 2)

    def test_update_outcome(self):
        outcome = LearningOutcome.objects.create(subject=self.subject, code="LO1", description="Original", order=1)
        updated = LearningOutcomeService.update_outcome(outcome, {"description": "Updated description", "order": 3})
        self.assertEqual(updated.description, "Updated description")
        self.assertEqual(updated.order, 3)

    def test_delete_outcome(self):
        outcome = LearningOutcome.objects.create(subject=self.subject, code="LO1", description="To delete", order=1)
        success = LearningOutcomeService.delete_outcome(outcome)
        self.assertTrue(success)
        with self.assertRaises(LearningOutcome.DoesNotExist):
            LearningOutcome.objects.get(id=outcome.id)

    def test_reorder_outcomes(self):
        o1 = LearningOutcome.objects.create(subject=self.subject, code="LO1", description="First", order=1)
        o2 = LearningOutcome.objects.create(subject=self.subject, code="LO2", description="Second", order=2)
        o3 = LearningOutcome.objects.create(subject=self.subject, code="LO3", description="Third", order=3)
        success = LearningOutcomeService.reorder_outcomes(self.subject.id, [o3.id, o1.id, o2.id])
        self.assertTrue(success)
        o1.refresh_from_db()
        o2.refresh_from_db()
        o3.refresh_from_db()
        self.assertEqual(o1.order, 2)
        self.assertEqual(o2.order, 3)
        self.assertEqual(o3.order, 1)


class LearningOutcomeSerializerTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(code="PHY101", name="Physics")

    def test_create_serializer_valid(self):
        data = {
            "subject_id": self.subject.id,
            "code": "LO1",
            "description": "Understand Newton's laws",
            "order": 1
        }
        serializer = LearningOutcomeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        outcome = serializer.save()
        self.assertEqual(outcome.subject, self.subject)

    def test_create_serializer_invalid_missing_code(self):
        data = {"subject_id": self.subject.id, "description": "Missing code", "order": 1}
        serializer = LearningOutcomeCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_update_serializer(self):
        outcome = LearningOutcome.objects.create(subject=self.subject, code="LO1", description="Original", order=1)
        data = {"description": "New description", "order": 5}
        serializer = LearningOutcomeUpdateSerializer(outcome, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.description, "New description")
        self.assertEqual(updated.order, 5)

    def test_display_serializer(self):
        outcome = LearningOutcome.objects.create(subject=self.subject, code="LO1", description="Test", order=1)
        serializer = LearningOutcomeDisplaySerializer(outcome)
        self.assertEqual(serializer.data["code"], "LO1")
        self.assertEqual(serializer.data["description"], "Test")