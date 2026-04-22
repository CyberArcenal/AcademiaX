from django.test import TestCase
from decimal import Decimal
from academic.models import Subject
from teachers.models import Teacher
from students.models import Student
from users.models import User
from assessments.models import Assessment, Question, Choice, Submission, Answer
from assessments.services.answer import AnswerService
from assessments.serializers.answer import (
    AnswerCreateSerializer,
    AnswerUpdateSerializer,
    AnswerDisplaySerializer,
)
from common.enums.assessment import AssessmentType, QuestionType, SubmissionStatus


class AnswerModelTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_ans", email="tans@example.com", password="test")
        self.user_student = User.objects.create_user(username="student_ans", email="sans@example.com", password="test")
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.teacher = Teacher.objects.create(
            user=self.user_teacher,
            first_name="John",
            last_name="Doe",
            birth_date="1980-01-01",
            gender="M",
            hire_date="2020-01-01"
        )
        self.student = Student.objects.create(
            user=self.user_student,
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2000-01-01",
            gender="M"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Math Quiz",
            assessment_type=AssessmentType.QUIZ
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            question_text="2+2 = ?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            points=5,
            order=1
        )
        self.choice = Choice.objects.create(
            question=self.question,
            choice_text="4",
            is_correct=True,
            order=1
        )
        self.submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student,
            status=SubmissionStatus.SUBMITTED
        )

    def test_create_answer_with_choice(self):
        answer = Answer.objects.create(
            submission=self.submission,
            question=self.question,
            selected_choice=self.choice,
            points_earned=5
        )
        self.assertEqual(answer.submission, self.submission)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.selected_choice, self.choice)

    def test_create_answer_with_text(self):
        answer = Answer.objects.create(
            submission=self.submission,
            question=self.question,
            text_answer="4",
            points_earned=5
        )
        self.assertEqual(answer.text_answer, "4")

    def test_str_method(self):
        answer = Answer.objects.create(
            submission=self.submission,
            question=self.question
        )
        expected = f"Answer for {self.submission} - Q{self.question.id}"
        self.assertEqual(str(answer), expected)


class AnswerServiceTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_ans_svc", email="tanssvc@example.com", password="test")
        self.user_student = User.objects.create_user(username="student_ans_svc", email="sanssvc@example.com", password="test")
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.teacher = Teacher.objects.create(
            user=self.user_teacher,
            first_name="Jane",
            last_name="Smith",
            birth_date="1985-01-01",
            gender="F",
            hire_date="2019-01-01"
        )
        self.student = Student.objects.create(
            user=self.user_student,
            first_name="Maria",
            last_name="Santos",
            birth_date="2001-02-02",
            gender="F"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Biology Quiz",
            assessment_type=AssessmentType.QUIZ
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            question_text="What is mitochondria?",
            question_type=QuestionType.ESSAY,
            points=10,
            order=1
        )
        self.submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student
        )

    def test_create_or_update_answer(self):
        answer = AnswerService.create_or_update_answer(
            submission=self.submission,
            question=self.question,
            text_answer="Powerhouse of the cell"
        )
        self.assertEqual(answer.submission, self.submission)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.text_answer, "Powerhouse of the cell")

    def test_get_answers_by_submission(self):
        Answer.objects.create(submission=self.submission, question=self.question, text_answer="Answer 1")
        answers = AnswerService.get_answers_by_submission(self.submission.id)
        self.assertEqual(answers.count(), 1)

    def test_grade_answer(self):
        answer = Answer.objects.create(submission=self.submission, question=self.question, text_answer="Test")
        graded = AnswerService.grade_answer(answer, points_earned=8, feedback="Good")
        self.assertEqual(graded.points_earned, 8)
        self.assertEqual(graded.feedback, "Good")


class AnswerSerializerTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_ans_ser", email="tansser@example.com", password="test")
        self.user_student = User.objects.create_user(username="student_ans_ser", email="sansser@example.com", password="test")
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.teacher = Teacher.objects.create(
            user=self.user_teacher,
            first_name="Mark",
            last_name="Brown",
            birth_date="1975-01-01",
            gender="M",
            hire_date="2015-01-01"
        )
        self.student = Student.objects.create(
            user=self.user_student,
            first_name="Pedro",
            last_name="Penduko",
            birth_date="2002-03-03",
            gender="M"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="English Quiz",
            assessment_type=AssessmentType.QUIZ
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            question_text="What is a noun?",
            question_type=QuestionType.ESSAY,
            order=1
        )
        self.submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student
        )

    def test_create_serializer_valid(self):
        data = {
            "submission_id": self.submission.id,
            "question_id": self.question.id,
            "text_answer": "A person, place, or thing"
        }
        serializer = AnswerCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        answer = serializer.save()
        self.assertEqual(answer.submission, self.submission)

    def test_update_serializer(self):
        answer = Answer.objects.create(submission=self.submission, question=self.question, text_answer="Old")
        data = {"points_earned": 5, "feedback": "Good effort"}
        serializer = AnswerUpdateSerializer(answer, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.points_earned, 5)

    def test_display_serializer(self):
        answer = Answer.objects.create(submission=self.submission, question=self.question, text_answer="Test")
        serializer = AnswerDisplaySerializer(answer)
        self.assertEqual(serializer.data["submission"]["id"], self.submission.id)
        self.assertEqual(serializer.data["question"]["id"], self.question.id)