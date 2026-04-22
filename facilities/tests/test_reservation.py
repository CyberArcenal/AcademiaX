from django.test import TestCase
from datetime import datetime, timedelta
from users.models import User
from facilities.models import Building, Facility, FacilityReservation
from facilities.services.reservation import FacilityReservationService
from facilities.serializers.reservation import (
    FacilityReservationCreateSerializer,
    FacilityReservationUpdateSerializer,
    FacilityReservationDisplaySerializer,
)
from common.enums.facilities import ReservationStatus


class FacilityReservationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", email="u1@example.com", password="test")
        self.building = Building.objects.create(name="Main", code="MAIN")
        self.facility = Facility.objects.create(building=self.building, name="Room 101")
        self.start = datetime.now() + timedelta(days=1)
        self.end = self.start + timedelta(hours=2)

    def test_create_reservation(self):
        reservation = FacilityReservation.objects.create(
            facility=self.facility,
            reserved_by=self.user,
            title="Meeting",
            purpose="Team meeting",
            start_datetime=self.start,
            end_datetime=self.end,
            status=ReservationStatus.PENDING
        )
        self.assertEqual(reservation.facility, self.facility)
        self.assertEqual(reservation.title, "Meeting")
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_str_method(self):
        reservation = FacilityReservation.objects.create(
            facility=self.facility,
            reserved_by=self.user,
            title="Event",
            start_datetime=self.start,
            end_datetime=self.end
        )
        expected = f"{self.facility.name} - Event ({self.start.date()})"
        self.assertEqual(str(reservation), expected)


class FacilityReservationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user2", email="u2@example.com", password="test")
        self.building = Building.objects.create(name="Science", code="SCI")
        self.facility = Facility.objects.create(building=self.building, name="Lab A")
        self.start = datetime.now() + timedelta(days=2)
        self.end = self.start + timedelta(hours=3)

    def test_create_reservation(self):
        reservation = FacilityReservationService.create_reservation(
            facility=self.facility,
            reserved_by=self.user,
            title="Experiment",
            purpose="Chemistry lab",
            start_datetime=self.start,
            end_datetime=self.end,
            attendees_count=10
        )
        self.assertEqual(reservation.facility, self.facility)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_prevent_overlap(self):
        FacilityReservationService.create_reservation(
            facility=self.facility, reserved_by=self.user, title="First",
            start_datetime=self.start, end_datetime=self.end
        )
        with self.assertRaises(Exception):
            FacilityReservationService.create_reservation(
                facility=self.facility, reserved_by=self.user, title="Second",
                start_datetime=self.start + timedelta(minutes=30),
                end_datetime=self.end + timedelta(minutes=30)
            )

    def test_approve_reservation(self):
        reservation = FacilityReservation.objects.create(
            facility=self.facility, reserved_by=self.user, title="Test",
            start_datetime=self.start, end_datetime=self.end, status=ReservationStatus.PENDING
        )
        approved = FacilityReservationService.approve_reservation(reservation, self.user)
        self.assertEqual(approved.status, ReservationStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.user)


class FacilityReservationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user3", email="u3@example.com", password="test")
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.facility = Facility.objects.create(building=self.building, name="Conference")
        self.start = datetime.now() + timedelta(days=3)
        self.end = self.start + timedelta(hours=2)

    def test_create_serializer_valid(self):
        data = {
            "facility_id": self.facility.id,
            "reserved_by_id": self.user.id,
            "title": "Board Meeting",
            "purpose": "Quarterly review",
            "start_datetime": self.start.isoformat(),
            "end_datetime": self.end.isoformat(),
            "attendees_count": 15
        }
        serializer = FacilityReservationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        reservation = serializer.save()
        self.assertEqual(reservation.facility, self.facility)

    def test_update_serializer(self):
        reservation = FacilityReservation.objects.create(
            facility=self.facility, reserved_by=self.user, title="Old",
            start_datetime=self.start, end_datetime=self.end
        )
        data = {"title": "Updated", "status": ReservationStatus.CANCELLED}
        serializer = FacilityReservationUpdateSerializer(reservation, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated")

    def test_display_serializer(self):
        reservation = FacilityReservation.objects.create(
            facility=self.facility, reserved_by=self.user, title="Display",
            start_datetime=self.start, end_datetime=self.end
        )
        serializer = FacilityReservationDisplaySerializer(reservation)
        self.assertEqual(serializer.data["title"], "Display")
        self.assertEqual(serializer.data["facility"]["id"], self.facility.id)