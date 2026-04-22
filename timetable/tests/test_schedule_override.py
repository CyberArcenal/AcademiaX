from django.test import TestCase
from datetime import time, date, timedelta
from users.models import User
from teachers.models import Teacher
from classes.models import AcademicYear, GradeLevel, Section, Term
from academic.models import Subject
from facilities.models import Building, Facility
from timetable.models import TimeSlot, Schedule, ScheduleOverride
from timetable.services.schedule_override import ScheduleOverrideService
from timetable.serializers.schedule_override import (
    ScheduleOverrideCreateSerializer,
    ScheduleOverrideUpdateSerializer,
    ScheduleOverrideDisplaySerializer,
)
from common.enums.timetable import DayOfWeek, ScheduleType


class ScheduleOverrideModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.term = Term.objects.create(academic_year=self.academic_year, term_type="QTR", term_number=1, name="Q1", start_date=date(2025,6,1), end_date=date(2025,8,15))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="A", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="MATH101", name="Algebra")
        self.user = User.objects.create_user(username="teacher", email="t@example.com", password="test")
        self.teacher = Teacher.objects.create(user=self.user, first_name="John", last_name="Doe", birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1))
        self.building = Building.objects.create(name="Main", code="MAIN")
        self.room = Facility.objects.create(building=self.building, name="Room 101")
        self.time_slot = TimeSlot.objects.create(name="Period 1", day_of_week=DayOfWeek.MONDAY, start_time=time(8,0), end_time=time(9,0), order=1, academic_year=self.academic_year)
        self.schedule = Schedule.objects.create(
            time_slot=self.time_slot, section=self.section, subject=self.subject,
            teacher=self.teacher, room=self.room, term=self.term
        )

    def test_create_override(self):
        override = ScheduleOverride.objects.create(
            schedule=self.schedule,
            date=date(2025, 6, 10),
            new_start_time=time(9, 0),
            new_end_time=time(10, 0),
            reason="Teacher training",
            is_cancelled=False
        )
        self.assertEqual(override.schedule, self.schedule)
        self.assertEqual(override.new_start_time, time(9,0))

    def test_str_method(self):
        override = ScheduleOverride.objects.create(schedule=self.schedule, date=date(2025,6,10))
        expected = f"Override for {self.schedule} on 2025-06-10"
        self.assertEqual(str(override), expected)


class ScheduleOverrideServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.term = Term.objects.create(academic_year=self.academic_year, term_type="QTR", term_number=1, name="Q1", start_date=date(2025,6,1), end_date=date(2025,8,15))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="B", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="SCI101", name="Biology")
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(user=self.user, first_name="Jane", last_name="Smith", birth_date=date(1985,1,1), gender="F", hire_date=date(2019,1,1))
        self.building = Building.objects.create(name="Science", code="SCI")
        self.room = Facility.objects.create(building=self.building, name="Lab A")
        self.time_slot = TimeSlot.objects.create(name="Period 2", day_of_week=DayOfWeek.TUESDAY, start_time=time(9,0), end_time=time(10,0), order=2, academic_year=self.academic_year)
        self.schedule = Schedule.objects.create(
            time_slot=self.time_slot, section=self.section, subject=self.subject,
            teacher=self.teacher, room=self.room, term=self.term
        )

    def test_create_override(self):
        override = ScheduleOverrideService.create_override(
            schedule=self.schedule,
            date=date(2025, 6, 15),
            new_room=self.room,
            reason="Room change"
        )
        self.assertEqual(override.schedule, self.schedule)

    def test_get_overrides_by_schedule(self):
        ScheduleOverride.objects.create(schedule=self.schedule, date=date(2025,6,15))
        ScheduleOverride.objects.create(schedule=self.schedule, date=date(2025,6,16))
        overrides = ScheduleOverrideService.get_overrides_by_schedule(self.schedule.id)
        self.assertEqual(overrides.count(), 2)

    def test_cancel_override(self):
        override = ScheduleOverride.objects.create(schedule=self.schedule, date=date(2025,6,20), is_cancelled=False)
        cancelled = ScheduleOverrideService.cancel_override(override)
        self.assertTrue(cancelled.is_cancelled)


class ScheduleOverrideSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.term = Term.objects.create(academic_year=self.academic_year, term_type="QTR", term_number=1, name="Q1", start_date=date(2025,6,1), end_date=date(2025,8,15))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(user=self.user, first_name="Mark", last_name="Brown", birth_date=date(1975,1,1), gender="M", hire_date=date(2015,1,1))
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.room = Facility.objects.create(building=self.building, name="Office")
        self.time_slot = TimeSlot.objects.create(name="Period 3", day_of_week=DayOfWeek.WEDNESDAY, start_time=time(10,0), end_time=time(11,0), order=3, academic_year=self.academic_year)
        self.schedule = Schedule.objects.create(
            time_slot=self.time_slot, section=self.section, subject=self.subject,
            teacher=self.teacher, room=self.room, term=self.term
        )

    def test_create_serializer_valid(self):
        data = {
            "schedule_id": self.schedule.id,
            "date": "2025-06-25",
            "reason": "Holiday makeup",
            "is_cancelled": True
        }
        serializer = ScheduleOverrideCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        override = serializer.save()
        self.assertEqual(override.schedule, self.schedule)

    def test_update_serializer(self):
        override = ScheduleOverride.objects.create(schedule=self.schedule, date=date(2025,6,25), reason="Original")
        data = {"reason": "Updated", "new_start_time": "09:30:00"}
        serializer = ScheduleOverrideUpdateSerializer(override, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.reason, "Updated")

    def test_display_serializer(self):
        override = ScheduleOverride.objects.create(schedule=self.schedule, date=date(2025,6,25))
        serializer = ScheduleOverrideDisplaySerializer(override)
        self.assertEqual(serializer.data["schedule"]["id"], self.schedule.id)
        self.assertEqual(serializer.data["date"], "2025-06-25")