from django.test import TestCase
from users.models import User
from parents.models import Parent
from parents.services.parent import ParentService
from parents.serializers.parent import (
    ParentCreateSerializer,
    ParentUpdateSerializer,
    ParentDisplaySerializer,
)
from common.enums.parents import ParentStatus


class ParentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="parent1", email="p1@example.com", password="test")

    def test_create_parent(self):
        parent = Parent.objects.create(
            user=self.user,
            contact_number="09123456789",
            occupation="Teacher",
            status=ParentStatus.ACTIVE
        )
        self.assertEqual(parent.user, self.user)
        self.assertEqual(parent.contact_number, "09123456789")

    def test_str_method(self):
        parent = Parent.objects.create(user=self.user)
        expected = f"{self.user.get_full_name()}"
        self.assertEqual(str(parent), expected)


class ParentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="parent2", email="p2@example.com", password="test")

    def test_create_parent(self):
        parent = ParentService.create_parent(
            user=self.user,
            contact_number="09987654321",
            occupation="Engineer",
            receive_notifications=True
        )
        self.assertEqual(parent.user, self.user)
        self.assertTrue(parent.receive_notifications)

    def test_get_parent_by_user(self):
        created = Parent.objects.create(user=self.user)
        fetched = ParentService.get_parent_by_user(self.user.id)
        self.assertEqual(fetched, created)

    def test_update_parent(self):
        parent = Parent.objects.create(user=self.user)
        updated = ParentService.update_parent(parent, {"contact_number": "09123456789", "status": ParentStatus.BLACKLISTED})
        self.assertEqual(updated.contact_number, "09123456789")
        self.assertEqual(updated.status, ParentStatus.BLACKLISTED)


class ParentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="parent3", email="p3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "user_id": self.user.id,
            "contact_number": "09123456789",
            "occupation": "Doctor"
        }
        serializer = ParentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        parent = serializer.save()
        self.assertEqual(parent.user, self.user)

    def test_update_serializer(self):
        parent = Parent.objects.create(user=self.user)
        data = {"contact_number": "09987654321", "status": ParentStatus.INACTIVE}
        serializer = ParentUpdateSerializer(parent, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.contact_number, "09987654321")

    def test_display_serializer(self):
        parent = Parent.objects.create(user=self.user, contact_number="09123456789")
        serializer = ParentDisplaySerializer(parent)
        self.assertEqual(serializer.data["contact_number"], "09123456789")
        self.assertEqual(serializer.data["user"]["id"], self.user.id)