from django.test import TestCase
from decimal import Decimal
from academic.models import Subject
from teachers.models import Teacher
from users.models import User
from assessments.models import Assessment, Question
from assessments.services.question import QuestionService
from assessments.serializers.question import (
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
    QuestionDisplaySerializer,
)
from common.enums.assessment import AssessmentType, QuestionType


class QuestionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_q", email="tq@example.com", password="test")
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            birth_date="1980-01-01",
            gender="M",
            hire_date="2020-01-01"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Math Quiz",
            assessment_type=AssessmentType.QUIZ,
            total_points=0
        )

    def test_create_question(self):
        question = Question.objects.create(
            assessment=self.assessment,
            question_text="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            points=5,
            order=1
        )
        self.assertEqual(question.assessment, self.assessment)
        self.assertEqual(question.question_text, "What is 2+2?")
        self.assertEqual(question.points, 5)

    def test_str_method(self):
        question = Question.objects.create(
            assessment=self.assessment,
            question_text="Complex question?",
            question_type=QuestionType.ESSAY,
            order=1
        )
        expected = f"{self.assessment.title} - Q1: Complex question?"
        self.assertEqual(str(question), expected)


class QuestionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_qs", email="tqs@example.com", password="test")
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            birth_date="1985-01-01",
            gender="F",
            hire_date="2019-01-01"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Biology Quiz",
            assessment_type=AssessmentType.QUIZ
        )

    def test_create_question(self):
        question = QuestionService.create_question(
            assessment=self.assessment,
            question_text="What is photosynthesis?",
            question_type=QuestionType.ESSAY,
            points=10,
            order=1
        )
        self.assertEqual(question.assessment, self.assessment)
        self.assertEqual(question.question_text, "What is photosynthesis?")

    def test_get_questions_by_assessment(self):
        Question.objects.create(assessment=self.assessment, question_text="Q1", question_type=QuestionType.MULTIPLE_CHOICE, order=1)
        Question.objects.create(assessment=self.assessment, question_text="Q2", question_type=QuestionType.TRUE_FALSE, order=2)
        questions = QuestionService.get_questions_by_assessment(self.assessment.id)
        self.assertEqual(questions.count(), 2)

    def test_update_question(self):
        question = Question.objects.create(
            assessment=self.assessment,
            question_text="Original text",
            question_type=QuestionType.MULTIPLE_CHOICE,
            order=1
        )
        updated = QuestionService.update_question(
            question,
            {"question_text": "Updated text", "points": 15}
        )
        self.assertEqual(updated.question_text, "Updated text")
        self.assertEqual(updated.points, 15)

    def test_reorder_questions(self):
        q1 = Question.objects.create(assessment=self.assessment, question_text="First", question_type=QuestionType.MULTIPLE_CHOICE, order=1)
        q2 = Question.objects.create(assessment=self.assessment, question_text="Second", question_type=QuestionType.MULTIPLE_CHOICE, order=2)
        q3 = Question.objects.create(assessment=self.assessment, question_text="Third", question_type=QuestionType.MULTIPLE_CHOICE, order=3)
        success = QuestionService.reorder_questions(self.assessment.id, [q3.id, q1.id, q2.id])
        self.assertTrue(success)
        q1.refresh_from_db()
        q2.refresh_from_db()
        q3.refresh_from_db()
        self.assertEqual(q1.order, 2)
        self.assertEqual(q2.order, 3)
        self.assertEqual(q3.order, 1)


class QuestionSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_ser", email="tser@example.com", password="test")
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Mark",
            last_name="Brown",
            birth_date="1975-01-01",
            gender="M",
            hire_date="2015-01-01"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="English Quiz",
            assessment_type=AssessmentType.QUIZ
        )

    def test_create_serializer_valid(self):
        data = {
            "assessment_id": self.assessment.id,
            "question_text": "What is a noun?",
            "question_type": QuestionType.ESSAY,
            "points": 5,
            "order": 1
        }
        serializer = QuestionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        question = serializer.save()
        self.assertEqual(question.assessment, self.assessment)

    def test_update_serializer(self):
        question = Question.objects.create(
            assessment=self.assessment,
            question_text="Original",
            question_type=QuestionType.MULTIPLE_CHOICE,
            order=1
        )
        data = {"question_text": "Updated", "points": 10}
        serializer = QuestionUpdateSerializer(question, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.question_text, "Updated")

    def test_display_serializer(self):
        question = Question.objects.create(
            assessment=self.assessment,
            question_text="Display test",
            question_type=QuestionType.TRUE_FALSE,
            order=1
        )
        serializer = QuestionDisplaySerializer(question)
        self.assertEqual(serializer.data["question_text"], "Display test")
        self.assertEqual(serializer.data["assessment"]["id"], self.assessment.id)