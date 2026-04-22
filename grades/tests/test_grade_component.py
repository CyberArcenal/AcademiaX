from django.test import TestCase
from decimal import Decimal
from datetime import date
from academic.models import Subject
from classes.models import AcademicYear, GradeLevel
from grades.models import GradeComponent
from grades.services.grade_component import GradeComponentService
from grades.serializers.grade_component import (
    GradeComponentCreateSerializer,
    GradeComponentUpdateSerializer,
    GradeComponentDisplaySerializer,
)


class GradeComponentModelTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_grade_component(self):
        component = GradeComponent.objects.create(
            name="Written Work",
            weight=Decimal('40.00'),
            subject=self.subject,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            is_active=True
        )
        self.assertEqual(component.name, "Written Work")
        self.assertEqual(component.weight, Decimal('40.00'))

    def test_str_method(self):
        component = GradeComponent.objects.create(
            name="Performance Task",
            weight=Decimal('30.00'),
            subject=self.subject,
            academic_year=self.academic_year,
            grade_level=self.grade_level
        )
        expected = f"{self.subject.code} - Performance Task (30.00%)"
        self.assertEqual(str(component), expected)


class GradeComponentServiceTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_component(self):
        component = GradeComponentService.create_component(
            name="Examination",
            weight=Decimal('30.00'),
            subject=self.subject,
            academic_year=self.academic_year,
            grade_level=self.grade_level
        )
        self.assertEqual(component.name, "Examination")

    def test_get_components_by_subject(self):
        GradeComponent.objects.create(name="Comp1", weight=50, subject=self.subject,
                                      academic_year=self.academic_year, grade_level=self.grade_level)
        GradeComponent.objects.create(name="Comp2", weight=50, subject=self.subject,
                                      academic_year=self.academic_year, grade_level=self.grade_level)
        components = GradeComponentService.get_components_by_subject(
            self.subject.id, self.academic_year.id, self.grade_level.id
        )
        self.assertEqual(components.count(), 2)

    def test_validate_weights(self):
        GradeComponent.objects.create(name="Comp1", weight=40, subject=self.subject,
                                      academic_year=self.academic_year, grade_level=self.grade_level)
        GradeComponent.objects.create(name="Comp2", weight=60, subject=self.subject,
                                      academic_year=self.academic_year, grade_level=self.grade_level)
        valid = GradeComponentService.validate_weights(self.subject.id, self.academic_year.id, self.grade_level.id)
        self.assertTrue(valid)


class GradeComponentSerializerTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_serializer_valid(self):
        data = {
            "name": "Recitation",
            "weight": "20.00",
            "subject_id": self.subject.id,
            "academic_year_id": self.academic_year.id,
            "grade_level_id": self.grade_level.id,
            "is_active": True
        }
        serializer = GradeComponentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        component = serializer.save()
        self.assertEqual(component.subject, self.subject)

    def test_update_serializer(self):
        component = GradeComponent.objects.create(
            name="Old", weight=10, subject=self.subject,
            academic_year=self.academic_year, grade_level=self.grade_level
        )
        data = {"name": "New", "weight": "25.00"}
        serializer = GradeComponentUpdateSerializer(component, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New")

    def test_display_serializer(self):
        component = GradeComponent.objects.create(
            name="Display", weight=15, subject=self.subject,
            academic_year=self.academic_year, grade_level=self.grade_level
        )
        serializer = GradeComponentDisplaySerializer(component)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["subject"]["id"], self.subject.id)