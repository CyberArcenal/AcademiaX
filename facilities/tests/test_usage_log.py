from django.test import TestCase
from datetime import datetime, timedelta
from users.models import User
from facilities.models import Building, Facility, FacilityReservation, FacilityUsageLog
from facilities.services.usage_log import FacilityUsageLogService
from facilities.serializers.usage_log import (
    FacilityUsageLogCreateSerializer,
    FacilityUsageLogUpdateSerializer,
    FacilityUsageLogDisplaySerializer,
)


class FacilityUsageLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", email="u1@example.com", password="test")
        self.building = Building.objects.create(name="Main", code="MAIN")
        self.facility = Facility.objects.create(building=self.building, name="Room 101")
        self.start = datetime.now()
        self.reservation = FacilityReservation.objects.create(
            facility=self.facility,
            reserved_by=self.user,
            title="Event",
            start_datetime=self.start,
            end_datetime=self.start + timedelta(hours=2)
        )

    def test_create_usage_log(self):
        log = FacilityUsageLog.objects.create(
            facility=self.facility,
            reservation=self.reservation,
            used_by=self.user,
            check_in=self.start,
            condition_before="Clean"
        )
        self.assertEqual(log.facility, self.facility)
        self.assertEqual(log.reservation, self.reservation)
        self.assertEqual(log.used_by, self.user)

    def test_str_method(self):
        log = FacilityUsageLog.objects.create(
            facility=self.facility,
            used_by=self.user,
            check_in=self.start
        )
        expected = f"{self.facility.name} - {self.start.date()}"
        self.assertEqual(str(log), expected)


class FacilityUsageLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user2", email="u2@example.com", password="test")
        self.building = Building.objects.create(name="Science", code="SCI")
        self.facility = Facility.objects.create(building=self.building, name="Lab A")
        self.start = datetime.now()
        self.reservation = FacilityReservation.objects.create(
            facility=self.facility,
            reserved_by=self.user,
            title="Experiment",
            start_datetime=self.start,
            end_datetime=self.start + timedelta(hours=2)
        )

    def test_create_usage_log(self):
        log = FacilityUsageLogService.create_usage_log(
            facility=self.facility,
            used_by=self.user,
            check_in=self.start,
            reservation=self.reservation,
            condition_before="Good"
        )
        self.assertEqual(log.facility, self.facility)
        self.assertEqual(log.reservation, self.reservation)

    def test_get_logs_by_facility(self):
        FacilityUsageLog.objects.create(facility=self.facility, used_by=self.user, check_in=self.start)
        FacilityUsageLog.objects.create(facility=self.facility, used_by=self.user, check_in=self.start + timedelta(days=1))
        logs = FacilityUsageLogService.get_logs_by_facility(self.facility.id)
        self.assertEqual(logs.count(), 2)

    def test_check_out(self):
        log = FacilityUsageLog.objects.create(facility=self.facility, used_by=self.user, check_in=self.start)
        checked_out = FacilityUsageLogService.check_out(log, condition_after="Messy", notes="Needs cleaning")
        self.assertIsNotNone(checked_out.check_out)
        self.assertEqual(checked_out.condition_after, "Messy")


class FacilityUsageLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user3", email="u3@example.com", password="test")
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.facility = Facility.objects.create(building=self.building, name="Office")
        self.start = datetime.now()
        self.reservation = FacilityReservation.objects.create(
            facility=self.facility,
            reserved_by=self.user,
            title="Meeting",
            start_datetime=self.start,
            end_datetime=self.start + timedelta(hours=1)
        )

    def test_create_serializer_valid(self):
        data = {
            "facility_id": self.facility.id,
            "used_by_id": self.user.id,
            "check_in": self.start.isoformat(),
            "reservation_id": self.reservation.id,
            "condition_before": "Clean"
        }
        serializer = FacilityUsageLogCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.facility, self.facility)

    def test_update_serializer_checkout(self):
        log = FacilityUsageLog.objects.create(facility=self.facility, used_by=self.user, check_in=self.start)
        data = {"check_out": (self.start + timedelta(hours=2)).isoformat(), "condition_after": "Used"}
        serializer = FacilityUsageLogUpdateSerializer(log, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertIsNotNone(updated.check_out)
        self.assertEqual(updated.condition_after, "Used")

    def test_display_serializer(self):
        log = FacilityUsageLog.objects.create(facility=self.facility, used_by=self.user, check_in=self.start)
        serializer = FacilityUsageLogDisplaySerializer(log)
        self.assertEqual(serializer.data["facility"]["id"], self.facility.id)
        self.assertEqual(serializer.data["used_by"]["id"], self.user.id)