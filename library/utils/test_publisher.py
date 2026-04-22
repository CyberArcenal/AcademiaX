from django.test import TestCase
from library.models import Publisher
from library.services.publisher import PublisherService
from library.serializers.publisher import (
    PublisherCreateSerializer,
    PublisherUpdateSerializer,
    PublisherDisplaySerializer,
)


class PublisherModelTest(TestCase):
    def test_create_publisher(self):
        publisher = Publisher.objects.create(
            name="Anvil Publishing",
            address="Pasig City",
            contact_number="02-1234567",
            email="info@anvil.com",
            website="www.anvil.com"
        )
        self.assertEqual(publisher.name, "Anvil Publishing")
        self.assertEqual(publisher.email, "info@anvil.com")

    def test_str_method(self):
        publisher = Publisher.objects.create(name="Ateneo Press")
        self.assertEqual(str(publisher), "Ateneo Press")


class PublisherServiceTest(TestCase):
    def test_create_publisher(self):
        publisher = PublisherService.create_publisher(
            name="UP Press",
            address="Quezon City",
            website="uppress.com"
        )
        self.assertEqual(publisher.name, "UP Press")

    def test_get_all_publishers(self):
        Publisher.objects.create(name="Publisher A")
        Publisher.objects.create(name="Publisher B")
        publishers = PublisherService.get_all_publishers()
        self.assertEqual(publishers.count(), 2)

    def test_update_publisher(self):
        publisher = Publisher.objects.create(name="Old Name")
        updated = PublisherService.update_publisher(publisher, {"name": "New Name", "contact_number": "123456"})
        self.assertEqual(updated.name, "New Name")


class PublisherSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": "Vibal Publishing",
            "address": "Manila",
            "website": "vibal.com"
        }
        serializer = PublisherCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        publisher = serializer.save()
        self.assertEqual(publisher.name, "Vibal Publishing")

    def test_update_serializer(self):
        publisher = Publisher.objects.create(name="Old Publisher")
        data = {"name": "Updated Publisher", "email": "new@email.com"}
        serializer = PublisherUpdateSerializer(publisher, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated Publisher")

    def test_display_serializer(self):
        publisher = Publisher.objects.create(name="Display Publisher")
        serializer = PublisherDisplaySerializer(publisher)
        self.assertEqual(serializer.data["name"], "Display Publisher")