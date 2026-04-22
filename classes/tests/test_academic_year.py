from django.test import TestCase
from datetime import date
from classes.models import AcademicYear
from classes.services.academic_year import AcademicYearService
from classes.serializers.academic_year import (
    AcademicYearCreateSerializer,
    AcademicYearUpdateSerializer,
    AcademicYearDisplaySerializer,
)


class AcademicYearModelTest(TestCase):
    def test_create_academic_year(self):
        year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31),
            is_current=True
        )
        self.assertEqual(year.name, "2025-2026")
        self.assertTrue(year.is_current)

    def test_str_method(self):
        year = AcademicYear.objects.create(name="2024-2025", start_date=date(2024,6,1), end_date=date(2025,5,31))
        self.assertEqual(str(year), "2024-2025")


class AcademicYearServiceTest(TestCase):
    def test_create_academic_year(self):
        year = AcademicYearService.create_academic_year(
            name="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_current=True
        )
        self.assertEqual(year.name, "2026-2027")

    def test_get_current_academic_year(self):
        AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31), is_current=False)
        current = AcademicYear.objects.create(name="2026-2027", start_date=date(2026,6,1), end_date=date(2027,5,31), is_current=True)
        fetched = AcademicYearService.get_current_academic_year()
        self.assertEqual(fetched, current)

    def test_set_current(self):
        year1 = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31), is_current=False)
        year2 = AcademicYear.objects.create(name="2026-2027", start_date=date(2026,6,1), end_date=date(2027,5,31), is_current=False)
        updated = AcademicYearService.set_current(year2)
        year1.refresh_from_db()
        self.assertTrue(updated.is_current)
        self.assertFalse(year1.is_current)

    def test_update_academic_year(self):
        year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        updated = AcademicYearService.update_academic_year(year, {"name": "2025-2026 Updated"})
        self.assertEqual(updated.name, "2025-2026 Updated")


class AcademicYearSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": "2027-2028",
            "start_date": "2027-06-01",
            "end_date": "2028-05-31",
            "is_current": True
        }
        serializer = AcademicYearCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        year = serializer.save()
        self.assertEqual(year.name, "2027-2028")

    def test_update_serializer(self):
        year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        data = {"is_current": True}
        serializer = AcademicYearUpdateSerializer(year, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_current)

    def test_display_serializer(self):
        year = AcademicYear.objects.create(name="2028-2029", start_date=date(2028,6,1), end_date=date(2029,5,31))
        serializer = AcademicYearDisplaySerializer(year)
        self.assertEqual(serializer.data["name"], "2028-2029")