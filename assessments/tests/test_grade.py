from django.test import TestCase
from decimal import Decimal
from academic.models import Subject
from teachers.models import Teacher
from students.models import Student
from users.models import User
from assessments.models import Assessment, Submission, AssessmentGrade
from assessments.services.grade import AssessmentGradeService
from assessments.serializers.grade import (
    AssessmentGradeCreateSerializer,
    AssessmentGradeUpdateSerializer,
    AssessmentGradeDisplaySerializer,
)
from common.enums.assessment import AssessmentType, SubmissionStatus


class AssessmentGradeModelTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_grade", email="tgrade@example.com", password="test")
        self.user_student = User.objects.create_user(username="student_grade", email="sgrade@example.com", password="test")
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
            total_points=100
        )
        self.submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student,
            status=SubmissionStatus.SUBMITTED
        )

    def test_create_grade(self):
        grade = AssessmentGrade.objects.create(
            submission=self.submission,
            raw_score=85,
            percentage_score=85.0,
            transmuted_grade=85.0,
            remarks="Passed"
        )
        self.assertEqual(grade.submission, self.submission)
        self.assertEqual(grade.raw_score, 85)
        self.assertEqual(grade.remarks, "Passed")

    def test_str_method(self):
        grade = AssessmentGrade.objects.create(
            submission=self.submission,
            raw_score=90
        )
        expected = f"Grade for {self.submission}"
        self.assertEqual(str(grade), expected)


class AssessmentGradeServiceTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_grade_svc", email="tgradesvc@example.com", password="test")
        self.user_student = User.objects.create_user(username="student_grade_svc", email="sgradesvc@example.com", password="test")
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
            total_points=50
        )
        self.submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student
        )

    def test_create_or_update_grade(self):
        grade = AssessmentGradeService.create_or_update_grade(
            submission=self.submission,
            raw_score=40,
            percentage_score=80.0
        )
        self.assertEqual(grade.submission, self.submission)
        self.assertEqual(grade.raw_score, 40)

    def test_get_grade_by_submission(self):
        AssessmentGrade.objects.create(submission=self.submission, raw_score=45)
        grade = AssessmentGradeService.get_grade_by_submission(self.submission.id)
        self.assertIsNotNone(grade)
        self.assertEqual(grade.raw_score, 45)

    def test_calculate_percentage(self):
        percentage = AssessmentGradeService.calculate_percentage(Decimal('75'), Decimal('100'))
        self.assertEqual(percentage, Decimal('75.00'))

    def test_delete_grade(self):
        grade = AssessmentGrade.objects.create(submission=self.submission, raw_score=30)
        success = AssessmentGradeService.delete_grade(grade)
        self.assertTrue(success)
        with self.assertRaises(AssessmentGrade.DoesNotExist):
            AssessmentGrade.objects.get(id=grade.id)


class AssessmentGradeSerializerTest(TestCase):
    def setUp(self):
        self.user_teacher = User.objects.create_user(username="teacher_grade_ser", email="tgradeser@example.com", password="test")
        self.user_student = User.objects.create_user(username="student_grade_ser", email="sgradeser@example.com", password="test")
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
            title="English Essay",
            assessment_type=AssessmentType.ASSIGNMENT,
            total_points=20
        )
        self.submission = Submission.objects.create(
            assessment=self.assessment,
            student=self.student
        )

    def test_create_serializer_valid(self):
        data = {
            "submission_id": self.submission.id,
            "raw_score": 18,
            "percentage_score": 90.0,
            "remarks": "Excellent"
        }
        serializer = AssessmentGradeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        grade = serializer.save()
        self.assertEqual(grade.submission, self.submission)

    def test_update_serializer(self):
        grade = AssessmentGrade.objects.create(submission=self.submission, raw_score=15)
        data = {"raw_score": 17, "remarks": "Good"}
        serializer = AssessmentGradeUpdateSerializer(grade, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.raw_score, 17)
        self.assertEqual(updated.remarks, "Good")

    def test_display_serializer(self):
        grade = AssessmentGrade.objects.create(submission=self.submission, raw_score=16)
        serializer = AssessmentGradeDisplaySerializer(grade)
        self.assertEqual(serializer.data["raw_score"], "16.00")
        self.assertEqual(serializer.data["submission"]["id"], self.submission.id)