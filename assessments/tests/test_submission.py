from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from academic.models import Subject
from teachers.models import Teacher
from students.models import Student
from users.models import User
from assessments.models import Assessment, Submission
from assessments.services.submission import SubmissionService
from assessments.serializers.submission import (
    SubmissionCreateSerializer,
    SubmissionUpdateSerializer,
    SubmissionDisplaySerializer,
)
from common.enums.assessment import AssessmentType, SubmissionStatus


class SubmissionModelTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_sub", email="tsub@example.com", password="test")
        self.user_student = User.objects.create_user(username="student1", email="s1@example.com", password="test")
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
            title="Math Exam",
            assessment_type=AssessmentType.EXAM,
            due_date=timezone.now() + timedelta(days=7)
        )

    def test_create_submission(self):
        submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student,
            status=SubmissionStatus.SUBMITTED
        )
        self.assertEqual(submission.assessment, self.assessment)
        self.assertEqual(submission.student, self.student)
        self.assertEqual(submission.status, SubmissionStatus.SUBMITTED)

    def test_str_method(self):
        submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student
        )
        expected = f"{self.student} - {self.assessment.title}"
        self.assertEqual(str(submission), expected)


class SubmissionServiceTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_sub_svc", email="tsvc@example.com", password="test")
        self.user_student = User.objects.create_user(username="student2", email="s2@example.com", password="test")
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
            title="Biology Exam",
            assessment_type=AssessmentType.EXAM,
            attempts_allowed=2
        )

    def test_create_submission(self):
        submission = SubmissionService.create_submission(
            assessment=self.assessment,
            student=self.student,
            ip_address="127.0.0.1"
        )
        self.assertEqual(submission.assessment, self.assessment)
        self.assertEqual(submission.student, self.student)

    def test_prevent_duplicate_submission(self):
        Submission.objects.create(assessment=self.assessment, student=self.student)
        with self.assertRaises(Exception):
            SubmissionService.create_submission(assessment=self.assessment, student=self.student)

    def test_get_submissions_by_assessment(self):
        Submission.objects.create(assessment=self.assessment, student=self.student)
        submissions = SubmissionService.get_submissions_by_assessment(self.assessment.id)
        self.assertEqual(submissions.count(), 1)

    def test_grade_submission(self):
        submission = Submission.objects.create(assessment=self.assessment, student=self.student)
        graded = SubmissionService.grade_submission(
            submission,
            score=85.0,
            graded_by_id=self.user_teacher.id,
            feedback="Good job!"
        )
        self.assertEqual(graded.score, 85.0)
        self.assertEqual(graded.status, SubmissionStatus.GRADED)
        self.assertIsNotNone(graded.graded_at)


class SubmissionSerializerTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_ser_sub", email="tsersub@example.com", password="test")
        self.user_student = User.objects.create_user(username="student3", email="s3@example.com", password="test")
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
            title="Grammar Test",
            assessment_type=AssessmentType.QUIZ
        )

    def test_create_serializer_valid(self):
        data = {
            "assessment_id": self.assessment.id,
            "student_id": self.student.id
        }
        serializer = SubmissionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        submission = serializer.save()
        self.assertEqual(submission.assessment, self.assessment)

    def test_update_serializer(self):
        submission = Submission.objects.create(assessment=self.assessment, student=self.student)
        data = {"score": 90, "feedback": "Excellent"}
        serializer = SubmissionUpdateSerializer(submission, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.score, 90)

    def test_display_serializer(self):
        submission = Submission.objects.create(assessment=self.assessment, student=self.student)
        serializer = SubmissionDisplaySerializer(submission)
        self.assertEqual(serializer.data["assessment"]["id"], self.assessment.id)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)