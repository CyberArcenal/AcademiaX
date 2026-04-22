from django.test import TestCase
from decimal import Decimal
from academic.models import Subject
from teachers.models import Teacher
from users.models import User
from assessments.models import Assessment, RubricCriterion, RubricLevel
from assessments.services.rubric import RubricCriterionService, RubricLevelService
from assessments.serializers.rubric import (
    RubricCriterionCreateSerializer,
    RubricCriterionUpdateSerializer,
    RubricCriterionDisplaySerializer,
    RubricLevelCreateSerializer,
    RubricLevelUpdateSerializer,
    RubricLevelDisplaySerializer,
)
from common.enums.assessment import AssessmentType


class RubricCriterionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_rubric", email="trub@example.com", password="test")
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
            title="Math Project",
            assessment_type=AssessmentType.PROJECT
        )

    def test_create_criterion(self):
        criterion = RubricCriterion.objects.create(
            assessment=self.assessment,
            name="Content",
            description="Accuracy of content",
            max_points=Decimal('20'),
            order=1
        )
        self.assertEqual(criterion.assessment, self.assessment)
        self.assertEqual(criterion.name, "Content")
        self.assertEqual(criterion.max_points, 20)

    def test_str_method(self):
        criterion = RubricCriterion.objects.create(
            assessment=self.assessment,
            name="Presentation",
            max_points=10
        )
        expected = f"{self.assessment.title} - Presentation"
        self.assertEqual(str(criterion), expected)


class RubricCriterionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_crit_svc", email="tcritsvc@example.com", password="test")
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
            title="Biology Lab",
            assessment_type=AssessmentType.PROJECT
        )

    def test_create_criterion(self):
        criterion = RubricCriterionService.create_criterion(
            assessment=self.assessment,
            name="Methodology",
            max_points=15,
            order=1
        )
        self.assertEqual(criterion.assessment, self.assessment)
        self.assertEqual(criterion.name, "Methodology")

    def test_get_criteria_by_assessment(self):
        RubricCriterion.objects.create(assessment=self.assessment, name="Criterion A", max_points=10, order=1)
        RubricCriterion.objects.create(assessment=self.assessment, name="Criterion B", max_points=20, order=2)
        criteria = RubricCriterionService.get_criteria_by_assessment(self.assessment.id)
        self.assertEqual(criteria.count(), 2)

    def test_update_criterion(self):
        criterion = RubricCriterion.objects.create(assessment=self.assessment, name="Old", max_points=5, order=1)
        updated = RubricCriterionService.update_criterion(
            criterion,
            {"name": "New", "max_points": 10}
        )
        self.assertEqual(updated.name, "New")
        self.assertEqual(updated.max_points, 10)


class RubricLevelModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_level", email="tlevel@example.com", password="test")
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
            title="Essay",
            assessment_type=AssessmentType.ASSIGNMENT
        )
        self.criterion = RubricCriterion.objects.create(
            assessment=self.assessment,
            name="Clarity",
            max_points=10,
            order=1
        )

    def test_create_level(self):
        level = RubricLevel.objects.create(
            criterion=self.criterion,
            level_name="Excellent",
            description="Clear and concise",
            points=Decimal('10')
        )
        self.assertEqual(level.criterion, self.criterion)
        self.assertEqual(level.level_name, "Excellent")
        self.assertEqual(level.points, 10)

    def test_str_method(self):
        level = RubricLevel.objects.create(
            criterion=self.criterion,
            level_name="Good",
            points=8
        )
        expected = f"{self.criterion.name} - Good: 8"
        self.assertEqual(str(level), expected)


class RubricLevelServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_level_svc", email="tlevelsvc@example.com", password="test")
        self.subject = Subject.objects.create(code="HIST101", name="History")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Sarah",
            last_name="Jones",
            birth_date="1982-01-01",
            gender="F",
            hire_date="2018-01-01"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="History Paper",
            assessment_type=AssessmentType.ASSIGNMENT
        )
        self.criterion = RubricCriterion.objects.create(
            assessment=self.assessment,
            name="Research",
            max_points=20,
            order=1
        )

    def test_create_level(self):
        level = RubricLevelService.create_level(
            criterion=self.criterion,
            level_name="Advanced",
            points=20
        )
        self.assertEqual(level.criterion, self.criterion)
        self.assertEqual(level.level_name, "Advanced")

    def test_get_levels_by_criterion(self):
        RubricLevel.objects.create(criterion=self.criterion, level_name="High", points=20)
        RubricLevel.objects.create(criterion=self.criterion, level_name="Medium", points=10)
        levels = RubricLevelService.get_levels_by_criterion(self.criterion.id)
        self.assertEqual(levels.count(), 2)

    def test_update_level(self):
        level = RubricLevel.objects.create(criterion=self.criterion, level_name="Basic", points=5)
        updated = RubricLevelService.update_level(level, {"level_name": "Proficient", "points": 15})
        self.assertEqual(updated.level_name, "Proficient")
        self.assertEqual(updated.points, 15)


class RubricSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher_rub_ser", email="trubser@example.com", password="test")
        self.subject = Subject.objects.create(code="PHY101", name="Physics")
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="Albert",
            last_name="Einstein",
            birth_date="1970-01-01",
            gender="M",
            hire_date="2000-01-01"
        )
        self.assessment = Assessment.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            title="Physics Lab Report",
            assessment_type=AssessmentType.PROJECT
        )
        self.criterion = RubricCriterion.objects.create(
            assessment=self.assessment,
            name="Data Analysis",
            max_points=30,
            order=1
        )

    def test_criterion_create_serializer_valid(self):
        data = {
            "assessment_id": self.assessment.id,
            "name": "Conclusion",
            "max_points": 10,
            "order": 2
        }
        serializer = RubricCriterionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        criterion = serializer.save()
        self.assertEqual(criterion.assessment, self.assessment)

    def test_criterion_update_serializer(self):
        data = {"name": "Updated Criterion", "max_points": 25}
        serializer = RubricCriterionUpdateSerializer(self.criterion, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated Criterion")

    def test_criterion_display_serializer(self):
        serializer = RubricCriterionDisplaySerializer(self.criterion)
        self.assertEqual(serializer.data["name"], "Data Analysis")
        self.assertEqual(serializer.data["assessment"]["id"], self.assessment.id)

    def test_level_create_serializer_valid(self):
        data = {
            "criterion_id": self.criterion.id,
            "level_name": "Excellent",
            "points": 30
        }
        serializer = RubricLevelCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        level = serializer.save()
        self.assertEqual(level.criterion, self.criterion)

    def test_level_update_serializer(self):
        level = RubricLevel.objects.create(criterion=self.criterion, level_name="Good", points=20)
        data = {"level_name": "Very Good", "points": 25}
        serializer = RubricLevelUpdateSerializer(level, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.level_name, "Very Good")

    def test_level_display_serializer(self):
        level = RubricLevel.objects.create(criterion=self.criterion, level_name="Satisfactory", points=15)
        serializer = RubricLevelDisplaySerializer(level)
        self.assertEqual(serializer.data["level_name"], "Satisfactory")
        self.assertEqual(serializer.data["criterion"]["id"], self.criterion.id)