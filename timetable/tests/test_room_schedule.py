from django.test import TestCase
from datetime import time, date, timedelta
from classes.models import AcademicYear
from facilities.models import Building, Facility
from timetable.models import TimeSlot, RoomSchedule
from timetable.services.room_schedule import RoomScheduleService
from timetable.serializers.room_schedule import (
    RoomScheduleCreateSerializer,
    RoomScheduleUpdateSerializer,
    RoomScheduleDisplaySerializer,
)
from common.enums.timetable import DayOfWeek


class RoomScheduleModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.building = Building.objects.create(name="Main", code="MAIN")
        self.room = Facility.objects.create(building=self.building, name="Room 101")
        self.time_slot = TimeSlot.objects.create(
            name="Period 1", day_of_week=DayOfWeek.MONDAY, start_time=time(8,0), end_time=time(9,0), order=1, academic_year=self.academic_year
        )

    def test_create_room_schedule(self):
        rs = RoomSchedule.objects.create(
            room=self.room,
            time_slot=self.time_slot,
            event_name="Faculty Meeting",
            description="Weekly meeting",
            date=date(2025, 6, 10),
            is_recurring=False
        )
        self.assertEqual(rs.room, self.room)
        self.assertEqual(rs.event_name, "Faculty Meeting")

    def test_str_method(self):
        rs = RoomSchedule.objects.create(room=self.room, time_slot=self.time_slot, event_name="Event", date=date(2025,6,10))
        expected = f"{self.room.name} - Event on 2025-06-10"
        self.assertEqual(str(rs), expected)


class RoomScheduleServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.building = Building.objects.create(name="Science", code="SCI")
        self.room = Facility.objects.create(building=self.building, name="Lab A")
        self.time_slot = TimeSlot.objects.create(
            name="Period 2", day_of_week=DayOfWeek.TUESDAY, start_time=time(9,0), end_time=time(10,0), order=2, academic_year=self.academic_year
        )

    def test_create_room_schedule(self):
        rs = RoomScheduleService.create_room_schedule(
            room=self.room,
            time_slot=self.time_slot,
            event_name="Exam",
            date=date(2025, 6, 15),
            description="Midterm exam"
        )
        self.assertEqual(rs.room, self.room)

    def test_get_schedules_by_room(self):
        RoomSchedule.objects.create(room=self.room, time_slot=self.time_slot, event_name="E1", date=date(2025,6,15))
        RoomSchedule.objects.create(room=self.room, time_slot=self.time_slot, event_name="E2", date=date(2025,6,16))
        schedules = RoomScheduleService.get_schedules_by_room(self.room.id)
        self.assertEqual(schedules.count(), 2)

    def test_get_room_availability(self):
        # Create a schedule that occupies a time slot
        RoomSchedule.objects.create(room=self.room, time_slot=self.time_slot, event_name="Busy", date=date(2025,6,20))
        available = RoomScheduleService.get_room_availability(self.room.id, date(2025,6,20))
        # The time_slot used should NOT be available; all others (if any) are available
        # Since only one time_slot exists in DB, available list should be empty
        self.assertEqual(len(available), 0)


class RoomScheduleSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.room = Facility.objects.create(building=self.building, name="Conference")
        self.time_slot = TimeSlot.objects.create(
            name="Period 3", day_of_week=DayOfWeek.WEDNESDAY, start_time=time(10,0), end_time=time(11,0), order=3, academic_year=self.academic_year
        )

    def test_create_serializer_valid(self):
        data = {
            "room_id": self.room.id,
            "time_slot_id": self.time_slot.id,
            "event_name": "Seminar",
            "date": "2025-06-30",
            "description": "Guest speaker"
        }
        serializer = RoomScheduleCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        rs = serializer.save()
        self.assertEqual(rs.room, self.room)

    def test_update_serializer(self):
        rs = RoomSchedule.objects.create(room=self.room, time_slot=self.time_slot, event_name="Old", date=date(2025,6,30))
        data = {"event_name": "New Event", "description": "Updated"}
        serializer = RoomScheduleUpdateSerializer(rs, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.event_name, "New Event")

    def test_display_serializer(self):
        rs = RoomSchedule.objects.create(room=self.room, time_slot=self.time_slot, event_name="Display", date=date(2025,6,30))
        serializer = RoomScheduleDisplaySerializer(rs)
        self.assertEqual(serializer.data["event_name"], "Display")
        self.assertEqual(serializer.data["room"]["id"], self.room.id)