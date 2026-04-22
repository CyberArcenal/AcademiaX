from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from academic.models import Subject
from teachers.models import Teacher
from users.models import User
from assessments.models import Assessment
from assessments.services.assessment import AssessmentService
from assessments.serializers.assessment import (
    AssessmentCreateSerializer,
    AssessmentUpdateSerializer,
    AssessmentDisplaySerializer,
)
from common.enums.assessment import AssessmentType


class AssessmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher1",
            email="teacher@example.com",
            password="testpass"
        )
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            birth_date="1980-01-01",
            gender="M",
            hire_date="2020-01-01"
        )

    def test_create_assessment(self):
        assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Midterm Exam",
            assessment_type=AssessmentType.EXAM,
            total_points=100,
            due_date=timezone.now() + timedelta(days=7)
        )
        self.assertEqual(assessment.subject, self.subject)
        self.assertEqual(assessment.teacher, self.teacher)
        self.assertEqual(assessment.title, "Midterm Exam")
        self.assertFalse(assessment.is_published)

    def test_str_method(self):
        assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Quiz 1",
            assessment_type=AssessmentType.QUIZ
        )
        expected = f"{self.subject.code} - Quiz 1"
        self.assertEqual(str(assessment), expected)


class AssessmentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            birth_date="1985-01-01",
            gender="F",
            hire_date="2019-01-01"
        )

    def test_create_assessment(self):
        assessment = AssessmentService.create_assessment(
            subject=self.subject,
            teacher=self.teacher,
            title="Final Exam",
            assessment_type=AssessmentType.EXAM,
            total_points=50
        )
        self.assertEqual(assessment.title, "Final Exam")
        self.assertEqual(assessment.total_points, 50)

    def test_publish_assessment(self):
        assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Test",
            assessment_type=AssessmentType.QUIZ
        )
        published = AssessmentService.publish_assessment(assessment)
        self.assertTrue(published.is_published)

    def test_get_assessments_by_subject(self):
        Assessment.objects.create(subject=self.subject, teacher=self.teacher, title="Quiz 1", assessment_type=AssessmentType.QUIZ)
        Assessment.objects.create(subject=self.subject, teacher=self.teacher, title="Quiz 2", assessment_type=AssessmentType.QUIZ)
        assessments = AssessmentService.get_assessments_by_subject(self.subject.id)
        self.assertEqual(assessments.count(), 2)


class AssessmentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.subject = Subject.objects.create(code="ENG101", name="English")
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
            "subject_id": self.subject.id,
            "teacher_id": self.teacher.id,
            "title": "Vocabulary Quiz",
            "assessment_type": AssessmentType.QUIZ,
            "total_points": 20
        }
        serializer = AssessmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        assessment = serializer.save()
        self.assertEqual(assessment.title, "Vocabulary Quiz")

    def test_update_serializer(self):
        assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Original",
            assessment_type=AssessmentType.QUIZ
        )
        data = {"title": "Updated Title", "total_points": 30}
        serializer = AssessmentUpdateSerializer(assessment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated Title")

    def test_display_serializer(self):
        assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Display Test",
            assessment_type=AssessmentType.ASSIGNMENT
        )
        serializer = AssessmentDisplaySerializer(assessment)
        self.assertEqual(serializer.data["title"], "Display Test")
        self.assertEqual(serializer.data["subject"]["id"], self.subject.id)