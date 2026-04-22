from django.test import TestCase
from facilities.models import Building
from facilities.services.building import BuildingService
from facilities.serializers.building import (
    BuildingCreateSerializer,
    BuildingUpdateSerializer,
    BuildingDisplaySerializer,
)


class BuildingModelTest(TestCase):
    def test_create_building(self):
        building = Building.objects.create(
            name="Main Building",
            code="MB",
            address="123 School St",
            number_of_floors=4,
            year_built=2010,
            is_active=True
        )
        self.assertEqual(building.name, "Main Building")
        self.assertEqual(building.code, "MB")

    def test_code_uppercase_auto(self):
        building = Building.objects.create(name="Annex", code="annex")
        self.assertEqual(building.code, "ANNEX")

    def test_str_method(self):
        building = Building.objects.create(name="Library", code="LIB")
        self.assertEqual(str(building), "Library")


class BuildingServiceTest(TestCase):
    def test_create_building(self):
        building = BuildingService.create_building(
            name="Science Building",
            code="SCI",
            address="North Wing",
            number_of_floors=3
        )
        self.assertEqual(building.name, "Science Building")

    def test_get_building_by_code(self):
        created = Building.objects.create(name="Gym", code="GYM")
        fetched = BuildingService.get_building_by_code("gym")
        self.assertEqual(fetched, created)

    def test_update_building(self):
        building = Building.objects.create(name="Old Name", code="OLD")
        updated = BuildingService.update_building(building, {"name": "New Name", "is_active": False})
        self.assertEqual(updated.name, "New Name")
        self.assertFalse(updated.is_active)


class BuildingSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": "Admin Building",
            "code": "ADMIN",
            "address": "Admin St",
            "number_of_floors": 2
        }
        serializer = BuildingCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        building = serializer.save()
        self.assertEqual(building.name, "Admin Building")

    def test_update_serializer(self):
        building = Building.objects.create(name="Old", code="OLD")
        data = {"name": "Updated", "is_active": False}
        serializer = BuildingUpdateSerializer(building, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated")

    def test_display_serializer(self):
        building = Building.objects.create(name="Display", code="DISP")
        serializer = BuildingDisplaySerializer(building)
        self.assertEqual(serializer.data["name"], "Display")