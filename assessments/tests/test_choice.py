from django.test import TestCase
from academic.models import Subject
from teachers.models import Teacher
from assessments.models import Assessment, Question, Choice
from assessments.services.choice import ChoiceService
from assessments.serializers.choice import (
    ChoiceCreateSerializer,
    ChoiceUpdateSerializer,
    ChoiceDisplaySerializer,
)
from common.enums.assessment import AssessmentType, QuestionType
from users.models.user import User


class ChoiceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_c", email="tc@example.com", password="test")
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
            assessment_type=AssessmentType.QUIZ
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            question_text="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            order=1
        )

    def test_create_choice(self):
        choice = Choice.objects.create(
            question=self.question,
            choice_text="4",
            is_correct=True,
            order=1
        )
        self.assertEqual(choice.question, self.question)
        self.assertEqual(choice.choice_text, "4")
        self.assertTrue(choice.is_correct)

    def test_str_method(self):
        choice = Choice.objects.create(
            question=self.question,
            choice_text="5",
            order=1
        )
        expected = f"{self.question.id} - 5"
        self.assertEqual(str(choice), expected)


class ChoiceServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_cs", email="tcs@example.com", password="test")
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
            title="Bio Quiz",
            assessment_type=AssessmentType.QUIZ
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            question_text="What is the powerhouse of the cell?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            order=1
        )

    def test_create_choice(self):
        choice = ChoiceService.create_choice(
            question=self.question,
            choice_text="Mitochondria",
            is_correct=True,
            order=1
        )
        self.assertEqual(choice.question, self.question)
        self.assertEqual(choice.choice_text, "Mitochondria")

    def test_get_choices_by_question(self):
        Choice.objects.create(question=self.question, choice_text="A", order=1)
        Choice.objects.create(question=self.question, choice_text="B", order=2)
        choices = ChoiceService.get_choices_by_question(self.question.id)
        self.assertEqual(choices.count(), 2)

    def test_update_choice(self):
        choice = Choice.objects.create(question=self.question, choice_text="Wrong", is_correct=False, order=1)
        updated = ChoiceService.update_choice(choice, {"choice_text": "Correct", "is_correct": True})
        self.assertEqual(updated.choice_text, "Correct")
        self.assertTrue(updated.is_correct)

    def test_bulk_create_choices(self):
        choices_data = [
            {"text": "Option A", "is_correct": False},
            {"text": "Option B", "is_correct": True},
            {"text": "Option C", "is_correct": False},
        ]
        choices = ChoiceService.bulk_create_choices(self.question, choices_data)
        self.assertEqual(len(choices), 3)
        self.assertTrue(choices[1].is_correct)


class ChoiceSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_ser_c", email="tserc@example.com", password="test")
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
            title="Grammar Quiz",
            assessment_type=AssessmentType.QUIZ
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            question_text="Which is correct?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            order=1
        )

    def test_create_serializer_valid(self):
        data = {
            "question_id": self.question.id,
            "choice_text": "I am going",
            "is_correct": True,
            "order": 1
        }
        serializer = ChoiceCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        choice = serializer.save()
        self.assertEqual(choice.question, self.question)

    def test_update_serializer(self):
        choice = Choice.objects.create(question=self.question, choice_text="Old", order=1)
        data = {"choice_text": "New", "is_correct": True}
        serializer = ChoiceUpdateSerializer(choice, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.choice_text, "New")

    def test_display_serializer(self):
        choice = Choice.objects.create(question=self.question, choice_text="Test", order=1)
        serializer = ChoiceDisplaySerializer(choice)
        self.assertEqual(serializer.data["choice_text"], "Test")
        self.assertEqual(serializer.data["question"]["id"], self.question.id)