from django.test import TestCase
from decimal import Decimal
from datetime import date
from classes.models import AcademicYear, GradeLevel
from academic.models import AcademicProgram
from fees.models import FeeStructure
from fees.services.fee_structure import FeeStructureService
from fees.serializers.fee_structure import (
    FeeStructureCreateSerializer,
    FeeStructureUpdateSerializer,
    FeeStructureDisplaySerializer,
)
from common.enums.fees import FeeCategory


class FeeStructureModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_fee_structure(self):
        fs = FeeStructure.objects.create(
            name="Tuition Fee",
            category=FeeCategory.TUITION,
            amount=Decimal('15000.00'),
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            is_mandatory=True,
            is_per_semester=True
        )
        self.assertEqual(fs.name, "Tuition Fee")
        self.assertEqual(fs.amount, Decimal('15000.00'))

    def test_str_method(self):
        fs = FeeStructure.objects.create(name="Lab Fee", amount=Decimal('500.00'), academic_year=self.academic_year)
        self.assertEqual(str(fs), "Lab Fee - 500.00")


class FeeStructureServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_fee_structure(self):
        fs = FeeStructureService.create_fee_structure(
            name="Library Fee",
            category=FeeCategory.LIBRARY,
            amount=Decimal('300.00'),
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            is_mandatory=False
        )
        self.assertEqual(fs.name, "Library Fee")

    def test_get_fee_structures_by_academic_year(self):
        FeeStructure.objects.create(name="Fee1", amount=100, academic_year=self.academic_year)
        FeeStructure.objects.create(name="Fee2", amount=200, academic_year=self.academic_year)
        fees = FeeStructureService.get_fee_structures_by_academic_year(self.academic_year.id)
        self.assertEqual(fees.count(), 2)


class FeeStructureSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_serializer_valid(self):
        data = {
            "name": "Computer Fee",
            "category": FeeCategory.COMPUTER,
            "amount": "1000.00",
            "academic_year_id": self.academic_year.id,
            "grade_level_id": self.grade_level.id,
            "is_mandatory": True
        }
        serializer = FeeStructureCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        fs = serializer.save()
        self.assertEqual(fs.academic_year, self.academic_year)

    def test_update_serializer(self):
        fs = FeeStructure.objects.create(name="Old", amount=100, academic_year=self.academic_year)
        data = {"name": "Updated", "amount": "150.00"}
        serializer = FeeStructureUpdateSerializer(fs, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")

    def test_display_serializer(self):
        fs = FeeStructure.objects.create(name="Display", amount=500, academic_year=self.academic_year)
        serializer = FeeStructureDisplaySerializer(fs)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["academic_year"]["id"], self.academic_year.id)