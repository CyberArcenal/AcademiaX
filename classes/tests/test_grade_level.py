from django.test import TestCase
from classes.models import GradeLevel
from classes.services.grade_level import GradeLevelService
from classes.serializers.grade_level import (
    GradeLevelCreateSerializer,
    GradeLevelUpdateSerializer,
    GradeLevelDisplaySerializer,
)
from common.enums.academic import GradeLevel as GradeLevelChoices


class GradeLevelModelTest(TestCase):
    def test_create_grade_level(self):
        grade = GradeLevel.objects.create(
            level=GradeLevelChoices.GRADE_7,
            name="Grade 7",
            order=7
        )
        self.assertEqual(grade.level, GradeLevelChoices.GRADE_7)
        self.assertEqual(grade.name, "Grade 7")
        self.assertEqual(grade.order, 7)

    def test_str_method(self):
        grade = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_12, name="Grade 12", order=12)
        self.assertEqual(str(grade), "Grade 12")


class GradeLevelServiceTest(TestCase):
    def test_create_grade_level(self):
        grade = GradeLevelService.create_grade_level(
            level=GradeLevelChoices.GRADE_1,
            name="Grade 1",
            order=1
        )
        self.assertEqual(grade.level, GradeLevelChoices.GRADE_1)

    def test_get_all_grade_levels(self):
        GradeLevel.objects.create(level=GradeLevelChoices.GRADE_7, name="Grade 7", order=7)
        GradeLevel.objects.create(level=GradeLevelChoices.GRADE_8, name="Grade 8", order=8)
        grades = GradeLevelService.get_all_grade_levels()
        self.assertEqual(grades.count(), 2)

    def test_update_grade_level(self):
        grade = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_9, name="Grade 9", order=9)
        updated = GradeLevelService.update_grade_level(grade, {"name": "Grade 9 - Junior", "order": 10})
        self.assertEqual(updated.name, "Grade 9 - Junior")
        self.assertEqual(updated.order, 10)

    def test_reorder_grade_levels(self):
        g1 = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_7, name="Grade 7", order=1)
        g2 = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_8, name="Grade 8", order=2)
        g3 = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_9, name="Grade 9", order=3)
        success = GradeLevelService.reorder_grade_levels([g3.id, g1.id, g2.id])
        self.assertTrue(success)
        g1.refresh_from_db()
        g2.refresh_from_db()
        g3.refresh_from_db()
        self.assertEqual(g1.order, 2)
        self.assertEqual(g2.order, 3)
        self.assertEqual(g3.order, 1)


class GradeLevelSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "level": GradeLevelChoices.GRADE_10,
            "name": "Grade 10",
            "order": 10
        }
        serializer = GradeLevelCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        grade = serializer.save()
        self.assertEqual(grade.level, GradeLevelChoices.GRADE_10)

    def test_update_serializer(self):
        grade = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_11, name="Grade 11", order=11)
        data = {"name": "Grade Eleven", "order": 12}
        serializer = GradeLevelUpdateSerializer(grade, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Grade Eleven")

    def test_display_serializer(self):
        grade = GradeLevel.objects.create(level=GradeLevelChoices.GRADE_12, name="Grade 12", order=12)
        serializer = GradeLevelDisplaySerializer(grade)
        self.assertEqual(serializer.data["name"], "Grade 12")
        self.assertEqual(serializer.data["level"], GradeLevelChoices.GRADE_12)