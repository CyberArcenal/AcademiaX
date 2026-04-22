from django.test import TestCase
from datetime import time, date
from users.models import User
from teachers.models import Teacher
from classes.models import AcademicYear, GradeLevel, Section, Term
from academic.models import Subject
from facilities.models import Building, Facility
from timetable.models import TimeSlot, Schedule
from timetable.services.schedule import ScheduleService
from timetable.serializers.schedule import (
    ScheduleCreateSerializer,
    ScheduleUpdateSerializer,
    ScheduleDisplaySerializer,
)
from common.enums.timetable import DayOfWeek, ScheduleType


class ScheduleModelTest(TestCase):
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

    def test_create_schedule(self):
        schedule = Schedule.objects.create(
            time_slot=self.time_slot,
            section=self.section,
            subject=self.subject,
            teacher=self.teacher,
            room=self.room,
            term=self.term,
            schedule_type=ScheduleType.REGULAR,
            is_active=True
        )
        self.assertEqual(schedule.section, self.section)
        self.assertEqual(schedule.teacher, self.teacher)

    def test_str_method(self):
        schedule = Schedule.objects.create(time_slot=self.time_slot, section=self.section, subject=self.subject, teacher=self.teacher, room=self.room, term=self.term)
        expected = f"{self.section} - {self.subject.code} - {self.time_slot}"
        self.assertEqual(str(schedule), expected)


class ScheduleServiceTest(TestCase):
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

    def test_create_schedule(self):
        schedule = ScheduleService.create_schedule(
            time_slot=self.time_slot,
            section=self.section,
            subject=self.subject,
            teacher=self.teacher,
            room=self.room,
            term=self.term
        )
        self.assertEqual(schedule.section, self.section)

    def test_prevent_conflict_section(self):
        ScheduleService.create_schedule(self.time_slot, self.section, self.subject, self.teacher, self.room, self.term)
        with self.assertRaises(Exception):
            ScheduleService.create_schedule(self.time_slot, self.section, self.subject, self.teacher, self.room, self.term)

    def test_prevent_conflict_teacher(self):
        ScheduleService.create_schedule(self.time_slot, self.section, self.subject, self.teacher, self.room, self.term)
        other_section = Section.objects.create(name="C", grade_level=self.grade_level, academic_year=self.academic_year)
        with self.assertRaises(Exception):
            ScheduleService.create_schedule(self.time_slot, other_section, self.subject, self.teacher, self.room, self.term)


class ScheduleSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.term = Term.objects.create(academic_year=self.academic_year, term_type="QTR", term_number=1, name="Q1", start_date=date(2025,6,1), end_date=date(2025,8,15))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(name="D", grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code="ENG101", name="English")
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(user=self.user, first_name="Mark", last_name="Brown", birth_date=date(1975,1,1), gender="M", hire_date=date(2015,1,1))
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.room = Facility.objects.create(building=self.building, name="Office")
        self.time_slot = TimeSlot.objects.create(name="Period 3", day_of_week=DayOfWeek.WEDNESDAY, start_time=time(10,0), end_time=time(11,0), order=3, academic_year=self.academic_year)

    def test_create_serializer_valid(self):
        data = {
            "time_slot_id": self.time_slot.id,
            "section_id": self.section.id,
            "subject_id": self.subject.id,
            "teacher_id": self.teacher.id,
            "room_id": self.room.id,
            "term_id": self.term.id,
            "schedule_type": ScheduleType.REGULAR
        }
        serializer = ScheduleCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        schedule = serializer.save()
        self.assertEqual(schedule.section, self.section)

    def test_update_serializer(self):
        schedule = Schedule.objects.create(time_slot=self.time_slot, section=self.section, subject=self.subject, teacher=self.teacher, room=self.room, term=self.term)
        data = {"schedule_type": ScheduleType.SPECIAL, "notes": "Special session"}
        serializer = ScheduleUpdateSerializer(schedule, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.schedule_type, ScheduleType.SPECIAL)

    def test_display_serializer(self):
        schedule = Schedule.objects.create(time_slot=self.time_slot, section=self.section, subject=self.subject, teacher=self.teacher, room=self.room, term=self.term)
        serializer = ScheduleDisplaySerializer(schedule)
        self.assertEqual(serializer.data["section"]["id"], self.section.id)
        self.assertEqual(serializer.data["subject"]["id"], self.subject.id)