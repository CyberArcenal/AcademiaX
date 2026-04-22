from django.test import TestCase
from facilities.models import Building, Facility
from facilities.services.facility import FacilityService
from facilities.serializers.facility import (
    FacilityCreateSerializer,
    FacilityUpdateSerializer,
    FacilityDisplaySerializer,
)
from common.enums.facilities import FacilityType, FacilityStatus


class FacilityModelTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Main", code="MAIN")

    def test_create_facility(self):
        facility = Facility.objects.create(
            building=self.building,
            name="Room 101",
            facility_type=FacilityType.CLASSROOM,
            room_number="101",
            floor=1,
            capacity=40,
            status=FacilityStatus.AVAILABLE,
            is_active=True
        )
        self.assertEqual(facility.building, self.building)
        self.assertEqual(facility.name, "Room 101")
        self.assertEqual(facility.facility_type, FacilityType.CLASSROOM)

    def test_str_method(self):
        facility = Facility.objects.create(building=self.building, name="Auditorium")
        expected = f"{self.building.name} - Auditorium (Auditorium)"
        self.assertEqual(str(facility), expected)


class FacilityServiceTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Science", code="SCI")

    def test_create_facility(self):
        facility = FacilityService.create_facility(
            building=self.building,
            name="Lab 1",
            facility_type=FacilityType.LABORATORY,
            capacity=30,
            features=["fume hood", "microscopes"]
        )
        self.assertEqual(facility.name, "Lab 1")
        self.assertEqual(facility.features, ["fume hood", "microscopes"])

    def test_get_facilities_by_building(self):
        Facility.objects.create(building=self.building, name="Room A")
        Facility.objects.create(building=self.building, name="Room B")
        facilities = FacilityService.get_facilities_by_building(self.building.id)
        self.assertEqual(facilities.count(), 2)

    def test_update_status(self):
        facility = Facility.objects.create(building=self.building, name="Gym", status=FacilityStatus.AVAILABLE)
        updated = FacilityService.update_status(facility, FacilityStatus.UNDER_MAINTENANCE)
        self.assertEqual(updated.status, FacilityStatus.UNDER_MAINTENANCE)


class FacilitySerializerTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Admin", code="ADM")

    def test_create_serializer_valid(self):
        data = {
            "building_id": self.building.id,
            "name": "Conference Room",
            "facility_type": FacilityType.OFFICE,
            "capacity": 20
        }
        serializer = FacilityCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        facility = serializer.save()
        self.assertEqual(facility.building, self.building)

    def test_update_serializer(self):
        facility = Facility.objects.create(building=self.building, name="Old Name")
        data = {"name": "New Name", "status": FacilityStatus.RESERVED}
        serializer = FacilityUpdateSerializer(facility, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.status, FacilityStatus.RESERVED)

    def test_display_serializer(self):
        facility = Facility.objects.create(building=self.building, name="Display", facility_type=FacilityType.LIBRARY)
        serializer = FacilityDisplaySerializer(facility)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["building"]["id"], self.building.id)