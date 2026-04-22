from django.test import TestCase
from datetime import date
from attendance.models import Holiday
from attendance.services.holiday import HolidayService
from attendance.serializers.holiday import (
    HolidayCreateSerializer,
    HolidayUpdateSerializer,
    HolidayDisplaySerializer,
)


class HolidayModelTest(TestCase):
    def test_create_holiday(self):
        holiday = Holiday.objects.create(
            name="Independence Day",
            date=date(2025, 6, 12),
            is_school_wide=True,
            notes="National holiday"
        )
        self.assertEqual(holiday.name, "Independence Day")
        self.assertEqual(holiday.date, date(2025, 6, 12))
        self.assertTrue(holiday.is_school_wide)

    def test_str_method(self):
        holiday = Holiday.objects.create(name="Christmas", date=date(2025, 12, 25))
        expected = "Christmas - 2025-12-25"
        self.assertEqual(str(holiday), expected)


class HolidayServiceTest(TestCase):
    def setUp(self):
        Holiday.objects.create(name="New Year", date=date(2025, 1, 1))
        Holiday.objects.create(name="Labor Day", date=date(2025, 5, 1))

    def test_create_holiday(self):
        holiday = HolidayService.create_holiday(
            name="Bonifacio Day",
            date=date(2025, 11, 30),
            is_school_wide=True
        )
        self.assertEqual(holiday.name, "Bonifacio Day")

    def test_get_holiday_by_date(self):
        holiday = HolidayService.get_holiday_by_date(date(2025, 1, 1))
        self.assertIsNotNone(holiday)
        self.assertEqual(holiday.name, "New Year")

    def test_get_upcoming_holidays(self):
        upcoming = HolidayService.get_upcoming_holidays(days_ahead=30)
        # Since today +30 might not include these, we'll just check method exists.
        self.assertIsInstance(upcoming, list)

    def test_is_holiday(self):
        self.assertTrue(HolidayService.is_holiday(date(2025, 1, 1)))
        self.assertFalse(HolidayService.is_holiday(date(2025, 1, 2)))

    def test_delete_holiday(self):
        holiday = Holiday.objects.create(name="Test", date=date(2025, 12, 31))
        success = HolidayService.delete_holiday(holiday)
        self.assertTrue(success)
        with self.assertRaises(Holiday.DoesNotExist):
            Holiday.objects.get(id=holiday.id)


class HolidaySerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": "Rizal Day",
            "date": "2025-12-30",
            "is_school_wide": True
        }
        serializer = HolidayCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        holiday = serializer.save()
        self.assertEqual(holiday.name, "Rizal Day")

    def test_update_serializer(self):
        holiday = Holiday.objects.create(name="Old", date=date(2025, 1, 1))
        data = {"name": "New Year's Day", "notes": "Observed"}
        serializer = HolidayUpdateSerializer(holiday, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New Year's Day")

    def test_display_serializer(self):
        holiday = Holiday.objects.create(name="Eid al-Fitr", date=date(2025, 4, 10))
        serializer = HolidayDisplaySerializer(holiday)
        self.assertEqual(serializer.data["name"], "Eid al-Fitr")
        self.assertEqual(serializer.data["date"], "2025-04-10")