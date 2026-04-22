from django.test import TestCase
from classes.models import Classroom
from classes.services.classroom import ClassroomService
from classes.serializers.classroom import (
    ClassroomCreateSerializer,
    ClassroomUpdateSerializer,
    ClassroomDisplaySerializer,
)
from common.enums.classes import RoomType


class ClassroomModelTest(TestCase):
    def test_create_classroom(self):
        classroom = Classroom.objects.create(
            room_number="101",
            building="Main Building",
            floor=1,
            capacity=40,
            room_type=RoomType.CLASSROOM,
            has_projector=True,
            has_aircon=False,
            is_active=True
        )
        self.assertEqual(classroom.room_number, "101")
        self.assertEqual(classroom.capacity, 40)
        self.assertTrue(classroom.has_projector)

    def test_str_method(self):
        classroom = Classroom.objects.create(room_number="201", building="Annex")
        expected = "201 (Regular Classroom)"
        self.assertEqual(str(classroom), expected)


class ClassroomServiceTest(TestCase):
    def test_create_classroom(self):
        classroom = ClassroomService.create_classroom(
            room_number="301",
            building="Science Building",
            floor=3,
            capacity=30,
            room_type=RoomType.LABORATORY,
            has_projector=True,
            has_aircon=True
        )
        self.assertEqual(classroom.room_number, "301")
        self.assertEqual(classroom.room_type, RoomType.LABORATORY)

    def test_get_classrooms_by_building(self):
        Classroom.objects.create(room_number="A101", building="Building A")
        Classroom.objects.create(room_number="A102", building="Building A")
        Classroom.objects.create(room_number="B101", building="Building B")
        classrooms = ClassroomService.get_classrooms_by_building("Building A")
        self.assertEqual(classrooms.count(), 2)

    def test_update_classroom(self):
        classroom = Classroom.objects.create(room_number="401", capacity=30)
        updated = ClassroomService.update_classroom(classroom, {"capacity": 35, "has_projector": True})
        self.assertEqual(updated.capacity, 35)
        self.assertTrue(updated.has_projector)

    def test_get_available_classrooms(self):
        # Simplified test: just ensure method exists and returns queryset
        available = ClassroomService.get_available_classrooms()
        self.assertIsNotNone(available)


class ClassroomSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "room_number": "501",
            "building": "Library",
            "floor": 2,
            "capacity": 50,
            "room_type": RoomType.AUDITORIUM,
            "has_projector": True
        }
        serializer = ClassroomCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        classroom = serializer.save()
        self.assertEqual(classroom.room_number, "501")

    def test_update_serializer(self):
        classroom = Classroom.objects.create(room_number="601", capacity=20)
        data = {"capacity": 25, "has_aircon": True}
        serializer = ClassroomUpdateSerializer(classroom, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.capacity, 25)

    def test_display_serializer(self):
        classroom = Classroom.objects.create(room_number="701", building="Gym", capacity=100)
        serializer = ClassroomDisplaySerializer(classroom)
        self.assertEqual(serializer.data["room_number"], "701")
        self.assertEqual(serializer.data["building"], "Gym")