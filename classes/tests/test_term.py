from django.test import TestCase
from datetime import date
from classes.models import AcademicYear, Term
from classes.services.term import TermService
from classes.serializers.term import (
    TermCreateSerializer,
    TermUpdateSerializer,
    TermDisplaySerializer,
)
from common.enums.classes import TermType


class TermModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31)
        )

    def test_create_term(self):
        term = Term.objects.create(
            academic_year=self.academic_year,
            term_type=TermType.SEMESTER,
            term_number=1,
            name="First Semester",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 10, 31),
            is_active=True
        )
        self.assertEqual(term.academic_year, self.academic_year)
        self.assertEqual(term.term_number, 1)
        self.assertTrue(term.is_active)

    def test_str_method(self):
        term = Term.objects.create(
            academic_year=self.academic_year,
            term_type=TermType.QUARTER,
            term_number=1,
            name="Quarter 1",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 8, 15)
        )
        expected = f"{self.academic_year.name} - Quarter 1"
        self.assertEqual(str(term), expected)


class TermServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31)
        )

    def test_create_term(self):
        term = TermService.create_term(
            academic_year=self.academic_year,
            term_type=TermType.SEMESTER,
            term_number=2,
            name="Second Semester",
            start_date=date(2025, 11, 1),
            end_date=date(2026, 3, 31),
            is_active=True
        )
        self.assertEqual(term.name, "Second Semester")
        self.assertEqual(term.term_number, 2)

    def test_get_terms_by_academic_year(self):
        Term.objects.create(academic_year=self.academic_year, term_type=TermType.SEMESTER, term_number=1, name="First", start_date=date(2025,6,1), end_date=date(2025,10,31))
        Term.objects.create(academic_year=self.academic_year, term_type=TermType.SEMESTER, term_number=2, name="Second", start_date=date(2025,11,1), end_date=date(2026,3,31))
        terms = TermService.get_terms_by_academic_year(self.academic_year.id)
        self.assertEqual(terms.count(), 2)

    def test_activate_term(self):
        term = Term.objects.create(academic_year=self.academic_year, term_type=TermType.SEMESTER, term_number=1, name="First", start_date=date(2025,6,1), end_date=date(2025,10,31), is_active=False)
        activated = TermService.activate_term(term)
        self.assertTrue(activated.is_active)

    def test_deactivate_term(self):
        term = Term.objects.create(academic_year=self.academic_year, term_type=TermType.SEMESTER, term_number=1, name="First", start_date=date(2025,6,1), end_date=date(2025,10,31), is_active=True)
        deactivated = TermService.deactivate_term(term)
        self.assertFalse(deactivated.is_active)


class TermSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31)
        )

    def test_create_serializer_valid(self):
        data = {
            "academic_year_id": self.academic_year.id,
            "term_type": TermType.QUARTER,
            "term_number": 1,
            "name": "Quarter 1",
            "start_date": "2025-06-01",
            "end_date": "2025-08-15",
            "is_active": True
        }
        serializer = TermCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        term = serializer.save()
        self.assertEqual(term.academic_year, self.academic_year)

    def test_update_serializer(self):
        term = Term.objects.create(academic_year=self.academic_year, term_type=TermType.SEMESTER, term_number=1, name="Old", start_date=date(2025,6,1), end_date=date(2025,10,31))
        data = {"name": "New Name", "is_active": False}
        serializer = TermUpdateSerializer(term, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New Name")
        self.assertFalse(updated.is_active)

    def test_display_serializer(self):
        term = Term.objects.create(academic_year=self.academic_year, term_type=TermType.SEMESTER, term_number=1, name="First Semester", start_date=date(2025,6,1), end_date=date(2025,10,31))
        serializer = TermDisplaySerializer(term)
        self.assertEqual(serializer.data["name"], "First Semester")
        self.assertEqual(serializer.data["academic_year"]["id"], self.academic_year.id)