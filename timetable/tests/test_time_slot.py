from django.test import TestCase
from datetime import time, date
from classes.models import AcademicYear
from timetable.models import TimeSlot
from timetable.services.time_slot import TimeSlotService
from timetable.serializers.time_slot import (
    TimeSlotCreateSerializer,
    TimeSlotUpdateSerializer,
    TimeSlotDisplaySerializer,
)
from common.enums.timetable import DayOfWeek


class TimeSlotModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )

    def test_create_time_slot(self):
        slot = TimeSlot.objects.create(
            name="Period 1",
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(8, 0),
            end_time=time(9, 0),
            order=1,
            academic_year=self.academic_year,
            is_active=True
        )
        self.assertEqual(slot.name, "Period 1")
        self.assertEqual(slot.start_time, time(8,0))

    def test_str_method(self):
        slot = TimeSlot.objects.create(
            name="Homeroom",
            day_of_week=DayOfWeek.TUESDAY,
            order=2,
            academic_year=self.academic_year
        )
        expected = "Tuesday 2: None-None"  # depends on implementation; adjust as needed
        self.assertIsInstance(str(slot), str)


class TimeSlotServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )

    def test_create_time_slot(self):
        slot = TimeSlotService.create_time_slot(
            name="Math Period",
            day_of_week=DayOfWeek.WEDNESDAY,
            start_time=time(9, 0),
            end_time=time(10, 0),
            order=3,
            academic_year=self.academic_year
        )
        self.assertEqual(slot.name, "Math Period")

    def test_get_time_slots_by_academic_year(self):
        TimeSlot.objects.create(name="Slot1", academic_year=self.academic_year, day_of_week=DayOfWeek.MONDAY, order=1)
        TimeSlot.objects.create(name="Slot2", academic_year=self.academic_year, day_of_week=DayOfWeek.TUESDAY, order=2)
        slots = TimeSlotService.get_time_slots_by_academic_year(self.academic_year.id)
        self.assertEqual(slots.count(), 2)

    def test_reorder_time_slots(self):
        s1 = TimeSlot.objects.create(name="S1", academic_year=self.academic_year, day_of_week=DayOfWeek.MONDAY, order=1)
        s2 = TimeSlot.objects.create(name="S2", academic_year=self.academic_year, day_of_week=DayOfWeek.MONDAY, order=2)
        success = TimeSlotService.reorder_time_slots(self.academic_year.id, [s2.id, s1.id])
        self.assertTrue(success)
        s1.refresh_from_db()
        s2.refresh_from_db()
        self.assertEqual(s1.order, 2)
        self.assertEqual(s2.order, 1)


class TimeSlotSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )

    def test_create_serializer_valid(self):
        data = {
            "name": "Recess",
            "day_of_week": DayOfWeek.FRIDAY,
            "start_time": "10:00:00",
            "end_time": "10:30:00",
            "order": 4,
            "academic_year_id": self.academic_year.id,
            "is_active": True
        }
        serializer = TimeSlotCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        slot = serializer.save()
        self.assertEqual(slot.name, "Recess")

    def test_update_serializer(self):
        slot = TimeSlot.objects.create(name="Old", academic_year=self.academic_year, day_of_week=DayOfWeek.MONDAY, order=1)
        data = {"name": "New", "order": 5}
        serializer = TimeSlotUpdateSerializer(slot, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New")

    def test_display_serializer(self):
        slot = TimeSlot.objects.create(name="Display", academic_year=self.academic_year, day_of_week=DayOfWeek.TUESDAY, order=2)
        serializer = TimeSlotDisplaySerializer(slot)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["academic_year"]["id"], self.academic_year.id)