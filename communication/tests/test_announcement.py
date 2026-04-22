from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User
from communication.models import Announcement
from communication.services.announcement import AnnouncementService
from communication.serializers.announcement import (
    AnnouncementCreateSerializer,
    AnnouncementUpdateSerializer,
    AnnouncementDisplaySerializer,
)
from common.enums.communication import TargetAudience, NotificationChannel


class AnnouncementModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_announcement(self):
        announcement = Announcement.objects.create(
            title="Test Announcement",
            content="This is a test",
            author=self.user,
            target_audience=TargetAudience.ALL,
            is_published=False
        )
        self.assertEqual(announcement.title, "Test Announcement")
        self.assertEqual(announcement.author, self.user)

    def test_str_method(self):
        announcement = Announcement.objects.create(title="Hello", author=self.user)
        self.assertEqual(str(announcement), "Hello")


class AnnouncementServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")

    def test_create_announcement(self):
        announcement = AnnouncementService.create_announcement(
            title="Service Test",
            content="Content",
            author=self.user,
            target_audience=TargetAudience.STUDENTS,
            channels=[NotificationChannel.IN_APP]
        )
        self.assertEqual(announcement.title, "Service Test")

    def test_publish_announcement(self):
        announcement = Announcement.objects.create(title="To Publish", author=self.user, is_published=False)
        published = AnnouncementService.publish_announcement(announcement)
        self.assertTrue(published.is_published)
        self.assertIsNotNone(published.published_at)

    def test_get_published_announcements(self):
        Announcement.objects.create(title="Published 1", author=self.user, is_published=True, published_at=timezone.now(), expires_at=timezone.now() + timedelta(days=7))
        Announcement.objects.create(title="Unpublished", author=self.user, is_published=False)
        published = AnnouncementService.get_published_announcements()
        self.assertEqual(published.count(), 1)


class AnnouncementSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", email="admin3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "title": "New Announcement",
            "content": "Content here",
            "author_id": self.user.id,
            "target_audience": TargetAudience.ALL,
            "channels": [NotificationChannel.IN_APP]
        }
        serializer = AnnouncementCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        announcement = serializer.save()
        self.assertEqual(announcement.author, self.user)

    def test_update_serializer(self):
        announcement = Announcement.objects.create(title="Old", author=self.user, content="Old content")
        data = {"title": "Updated", "content": "New content"}
        serializer = AnnouncementUpdateSerializer(announcement, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated")

    def test_display_serializer(self):
        announcement = Announcement.objects.create(title="Display Test", author=self.user)
        serializer = AnnouncementDisplaySerializer(announcement)
        self.assertEqual(serializer.data["title"], "Display Test")
        self.assertEqual(serializer.data["author"]["id"], self.user.id)