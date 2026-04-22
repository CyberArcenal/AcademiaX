from django.test import TestCase
from datetime import datetime, date, timedelta
from students.models import Student
from alumni.models import Alumni, AlumniEvent, EventAttendance
from alumni.services.event import AlumniEventService, EventAttendanceService
from alumni.serializers.event import (
    AlumniEventCreateSerializer,
    AlumniEventUpdateSerializer,
    AlumniEventDisplaySerializer,
    EventAttendanceCreateSerializer,
    EventAttendanceUpdateSerializer,
    EventAttendanceDisplaySerializer,
)
from common.enums.alumni import RSVPStatus


class AlumniEventModelTest(TestCase):
    def setUp(self):
        self.event_date = datetime.now() + timedelta(days=30)
        self.deadline = datetime.now() + timedelta(days=25)

    def test_create_event(self):
        event = AlumniEvent.objects.create(
            title="Homecoming 2025",
            description="Annual alumni homecoming",
            event_date=self.event_date,
            location="Main Campus",
            max_attendees=200,
            registration_deadline=self.deadline
        )
        self.assertEqual(event.title, "Homecoming 2025")
        self.assertEqual(event.location, "Main Campus")
        self.assertEqual(event.max_attendees, 200)

    def test_str_method(self):
        event = AlumniEvent.objects.create(
            title="Test Event",
            event_date=self.event_date,
            location="Online"
        )
        expected = f"Test Event - {self.event_date.date()}"
        self.assertEqual(str(event), expected)


class AlumniEventServiceTest(TestCase):
    def setUp(self):
        self.event_date = datetime.now() + timedelta(days=30)
        self.deadline = datetime.now() + timedelta(days=25)

    def test_create_event(self):
        event = AlumniEventService.create_event(
            title="Reunion 2025",
            event_date=self.event_date,
            location="Grand Ballroom",
            registration_deadline=self.deadline,
            max_attendees=100
        )
        self.assertEqual(event.title, "Reunion 2025")
        self.assertEqual(event.location, "Grand Ballroom")

    def test_get_upcoming_events(self):
        past = AlumniEvent.objects.create(
            title="Past Event",
            event_date=datetime.now() - timedelta(days=1),
            location="Old Site",
            registration_deadline=datetime.now() - timedelta(days=2)
        )
        upcoming = AlumniEvent.objects.create(
            title="Upcoming Event",
            event_date=datetime.now() + timedelta(days=10),
            location="New Site",
            registration_deadline=datetime.now() + timedelta(days=5)
        )
        upcoming_events = AlumniEventService.get_upcoming_events()
        self.assertIn(upcoming, upcoming_events)
        self.assertNotIn(past, upcoming_events)

    def test_update_event(self):
        event = AlumniEvent.objects.create(
            title="Original",
            event_date=self.event_date,
            location="Place A",
            registration_deadline=self.deadline
        )
        updated = AlumniEventService.update_event(
            event,
            {"title": "Updated Title", "max_attendees": 150}
        )
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.max_attendees, 150)


class EventAttendanceModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2000-01-01",
            gender="M"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )
        self.event = AlumniEvent.objects.create(
            title="Test Event",
            event_date=datetime.now() + timedelta(days=10),
            location="Test Location",
            registration_deadline=datetime.now() + timedelta(days=5)
        )

    def test_create_attendance(self):
        attendance = EventAttendance.objects.create(
            alumni=self.alumni,
            event=self.event,
            rsvp_status=RSVPStatus.GOING,
            attended=False
        )
        self.assertEqual(attendance.alumni, self.alumni)
        self.assertEqual(attendance.event, self.event)
        self.assertEqual(attendance.rsvp_status, RSVPStatus.GOING)

    def test_unique_together(self):
        EventAttendance.objects.create(alumni=self.alumni, event=self.event)
        with self.assertRaises(Exception):
            EventAttendance.objects.create(alumni=self.alumni, event=self.event)


class EventAttendanceServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria",
            last_name="Santos",
            birth_date="2001-02-02",
            gender="F"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )
        self.event = AlumniEvent.objects.create(
            title="Homecoming",
            event_date=datetime.now() + timedelta(days=10),
            location="Campus",
            registration_deadline=datetime.now() + timedelta(days=5)
        )

    def test_create_attendance(self):
        attendance = EventAttendanceService.create_attendance(
            alumni=self.alumni,
            event=self.event,
            rsvp_status=RSVPStatus.MAYBE
        )
        self.assertEqual(attendance.alumni, self.alumni)
        self.assertEqual(attendance.event, self.event)

    def test_get_attendances_by_event(self):
        EventAttendance.objects.create(alumni=self.alumni, event=self.event)
        attendances = EventAttendanceService.get_attendances_by_event(self.event.id)
        self.assertEqual(attendances.count(), 1)

    def test_update_rsvp(self):
        attendance = EventAttendance.objects.create(alumni=self.alumni, event=self.event, rsvp_status=RSVPStatus.NO_RESPONSE)
        updated = EventAttendanceService.update_rsvp(attendance, RSVPStatus.GOING)
        self.assertEqual(updated.rsvp_status, RSVPStatus.GOING)

    def test_mark_attended(self):
        attendance = EventAttendance.objects.create(alumni=self.alumni, event=self.event, attended=False)
        updated = EventAttendanceService.mark_attended(attendance)
        self.assertTrue(updated.attended)
        self.assertIsNotNone(updated.checked_in_at)


class EventSerializerTest(TestCase):
    def setUp(self):
        self.event_date = datetime.now() + timedelta(days=30)
        self.deadline = datetime.now() + timedelta(days=25)
        self.student = Student.objects.create(
            first_name="Pedro",
            last_name="Penduko",
            birth_date="2002-03-03",
            gender="M"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )
        self.event = AlumniEvent.objects.create(
            title="Test Event",
            event_date=self.event_date,
            location="Test",
            registration_deadline=self.deadline
        )

    def test_event_create_serializer_valid(self):
        data = {
            "title": "New Event",
            "event_date": self.event_date.isoformat(),
            "location": "New Location",
            "registration_deadline": self.deadline.isoformat()
        }
        serializer = AlumniEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        event = serializer.save()
        self.assertEqual(event.title, "New Event")

    def test_event_update_serializer(self):
        data = {"title": "Updated Event", "max_attendees": 300}
        serializer = AlumniEventUpdateSerializer(self.event, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated Event")

    def test_attendance_create_serializer_valid(self):
        data = {
            "alumni_id": self.alumni.id,
            "event_id": self.event.id,
            "rsvp_status": RSVPStatus.GOING
        }
        serializer = EventAttendanceCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        attendance = serializer.save()
        self.assertEqual(attendance.alumni, self.alumni)

    def test_attendance_update_serializer(self):
        attendance = EventAttendance.objects.create(alumni=self.alumni, event=self.event)
        data = {"rsvp_status": RSVPStatus.NOT_GOING}
        serializer = EventAttendanceUpdateSerializer(attendance, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.rsvp_status, RSVPStatus.NOT_GOING)

    def test_attendance_display_serializer(self):
        attendance = EventAttendance.objects.create(alumni=self.alumni, event=self.event)
        serializer = EventAttendanceDisplaySerializer(attendance)
        self.assertEqual(serializer.data["alumni"]["id"], self.alumni.id)
        self.assertEqual(serializer.data["event"]["id"], self.event.id)