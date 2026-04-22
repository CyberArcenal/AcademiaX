from django.test import TestCase
from datetime import date
from facilities.models import Building, Facility, Equipment
from facilities.services.equipment import EquipmentService
from facilities.serializers.equipment import (
    EquipmentCreateSerializer,
    EquipmentUpdateSerializer,
    EquipmentDisplaySerializer,
)


class EquipmentModelTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Main", code="MAIN")
        self.facility = Facility.objects.create(
            building=self.building,
            name="Room 101",
            facility_type="CR"
        )

    def test_create_equipment(self):
        equipment = Equipment.objects.create(
            facility=self.facility,
            name="Projector",
            serial_number="PRJ-001",
            model="Epson EB-FH06",
            manufacturer="Epson",
            purchase_date=date(2025, 1, 15),
            status="OPERATIONAL"
        )
        self.assertEqual(equipment.facility, self.facility)
        self.assertEqual(equipment.name, "Projector")
        self.assertEqual(equipment.serial_number, "PRJ-001")

    def test_serial_number_unique(self):
        Equipment.objects.create(name="Item1", serial_number="SN-001")
        with self.assertRaises(Exception):
            Equipment.objects.create(name="Item2", serial_number="SN-001")

    def test_str_method(self):
        equipment = Equipment.objects.create(name="Microscope", serial_number="MIC-001")
        expected = "Microscope (MIC-001)"
        self.assertEqual(str(equipment), expected)


class EquipmentServiceTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Science", code="SCI")
        self.facility = Facility.objects.create(building=self.building, name="Lab A")

    def test_create_equipment(self):
        equipment = EquipmentService.create_equipment(
            name="Centrifuge",
            serial_number="CEN-123",
            facility=self.facility,
            model="Model X",
            manufacturer="Brand A",
            purchase_date=date(2025, 2, 1),
            status="OPERATIONAL"
        )
        self.assertEqual(equipment.name, "Centrifuge")
        self.assertEqual(equipment.facility, self.facility)

    def test_get_equipment_by_facility(self):
        Equipment.objects.create(name="Item1", serial_number="S1", facility=self.facility)
        Equipment.objects.create(name="Item2", serial_number="S2", facility=self.facility)
        items = EquipmentService.get_equipment_by_facility(self.facility.id)
        self.assertEqual(items.count(), 2)

    def test_update_equipment_status(self):
        equipment = Equipment.objects.create(name="Fridge", serial_number="FR-001", status="OPERATIONAL")
        updated = EquipmentService.update_equipment_status(equipment, "NEEDS_REPAIR")
        self.assertEqual(updated.status, "NEEDS_REPAIR")


class EquipmentSerializerTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Admin", code="ADM")
        self.facility = Facility.objects.create(building=self.building, name="Office")

    def test_create_serializer_valid(self):
        data = {
            "name": "Laptop",
            "serial_number": "LAP-001",
            "facility_id": self.facility.id,
            "model": "Dell XPS",
            "manufacturer": "Dell"
        }
        serializer = EquipmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        equipment = serializer.save()
        self.assertEqual(equipment.facility, self.facility)

    def test_update_serializer(self):
        equipment = Equipment.objects.create(name="Old", serial_number="OLD-001")
        data = {"name": "Updated", "status": "UNDER_REPAIR"}
        serializer = EquipmentUpdateSerializer(equipment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")
        self.assertEqual(updated.status, "UNDER_REPAIR")

    def test_display_serializer(self):
        equipment = Equipment.objects.create(name="Display", serial_number="DISP-001")
        serializer = EquipmentDisplaySerializer(equipment)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["serial_number"], "DISP-001")