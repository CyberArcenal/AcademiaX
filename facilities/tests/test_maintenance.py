from django.test import TestCase
from datetime import date
from users.models import User
from facilities.models import Building, Facility, Equipment, MaintenanceRequest
from facilities.services.maintenance import MaintenanceRequestService
from facilities.serializers.maintenance import (
    MaintenanceRequestCreateSerializer,
    MaintenanceRequestUpdateSerializer,
    MaintenanceRequestDisplaySerializer,
)
from common.enums.facilities import MaintenancePriority, MaintenanceStatus


class MaintenanceRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", email="staff@example.com", password="test")
        self.building = Building.objects.create(name="Main", code="MAIN")
        self.facility = Facility.objects.create(building=self.building, name="Room 101")
        self.equipment = Equipment.objects.create(name="AC Unit", serial_number="AC-001")

    def test_create_maintenance_request_for_facility(self):
        req = MaintenanceRequest.objects.create(
            facility=self.facility,
            reported_by=self.user,
            title="Broken window",
            description="Window won't close",
            priority=MaintenancePriority.MEDIUM,
            status=MaintenanceStatus.PENDING
        )
        self.assertEqual(req.facility, self.facility)
        self.assertEqual(req.title, "Broken window")

    def test_create_maintenance_request_for_equipment(self):
        req = MaintenanceRequest.objects.create(
            equipment=self.equipment,
            reported_by=self.user,
            title="AC not cooling",
            description="Blowing warm air",
            priority=MaintenancePriority.HIGH
        )
        self.assertEqual(req.equipment, self.equipment)

    def test_str_method(self):
        req = MaintenanceRequest.objects.create(
            reported_by=self.user,
            title="Test Request",
            priority=MaintenancePriority.LOW
        )
        expected = "Test Request - Pending"
        self.assertEqual(str(req), expected)


class MaintenanceRequestServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff2", email="staff2@example.com", password="test")
        self.building = Building.objects.create(name="Science", code="SCI")
        self.facility = Facility.objects.create(building=self.building, name="Lab A")
        self.equipment = Equipment.objects.create(name="Microscope", serial_number="MIC-001")

    def test_create_request_for_facility(self):
        req = MaintenanceRequestService.create_request(
            reported_by=self.user,
            title="Leaking pipe",
            description="Water leak near sink",
            facility=self.facility,
            priority=MaintenancePriority.URGENT
        )
        self.assertEqual(req.facility, self.facility)
        self.assertEqual(req.status, MaintenanceStatus.PENDING)

    def test_get_pending_requests(self):
        MaintenanceRequest.objects.create(reported_by=self.user, title="Req1", status=MaintenanceStatus.PENDING)
        MaintenanceRequest.objects.create(reported_by=self.user, title="Req2", status=MaintenanceStatus.IN_PROGRESS)
        pending = MaintenanceRequestService.get_pending_requests()
        self.assertEqual(pending.count(), 1)

    def test_update_status_to_completed(self):
        req = MaintenanceRequest.objects.create(reported_by=self.user, title="Fix light", status=MaintenanceStatus.PENDING)
        updated = MaintenanceRequestService.update_status(
            req, MaintenanceStatus.COMPLETED, completed_date=date.today(), cost=500, remarks="Replaced bulb"
        )
        self.assertEqual(updated.status, MaintenanceStatus.COMPLETED)
        self.assertEqual(updated.completed_date, date.today())
        self.assertEqual(updated.cost, 500)


class MaintenanceRequestSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.facility = Facility.objects.create(building=self.building, name="Office")

    def test_create_serializer_valid(self):
        data = {
            "facility_id": self.facility.id,
            "reported_by_id": self.user.id,
            "title": "Door repair",
            "description": "Door handle broken",
            "priority": MaintenancePriority.MEDIUM
        }
        serializer = MaintenanceRequestCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        req = serializer.save()
        self.assertEqual(req.facility, self.facility)

    def test_update_serializer(self):
        req = MaintenanceRequest.objects.create(reported_by=self.user, title="Old title")
        data = {"title": "New title", "priority": MaintenancePriority.HIGH}
        serializer = MaintenanceRequestUpdateSerializer(req, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "New title")

    def test_display_serializer(self):
        req = MaintenanceRequest.objects.create(reported_by=self.user, title="Display Test")
        serializer = MaintenanceRequestDisplaySerializer(req)
        self.assertEqual(serializer.data["title"], "Display Test")
        self.assertEqual(serializer.data["reported_by"]["id"], self.user.id)