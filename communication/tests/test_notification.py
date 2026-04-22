from django.test import TestCase
from django.utils import timezone
from users.models import User
from communication.models import Notification
from communication.services.notification import NotificationService
from communication.serializers.notification import (
    NotificationCreateSerializer,
    NotificationUpdateSerializer,
    NotificationDisplaySerializer,
)
from common.enums.communication import NotificationType, NotificationChannel


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="recipient", email="rec@example.com", password="test")

    def test_create_notification(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Test Notification",
            message="This is a test",
            notification_type=NotificationType.INFO,
            channel=NotificationChannel.IN_APP,
            is_read=False
        )
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, "Test Notification")

    def test_str_method(self):
        notification = Notification.objects.create(recipient=self.user, title="Hello")
        expected = f"{self.user} - Hello"
        self.assertEqual(str(notification), expected)


class NotificationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="recipient2", email="rec2@example.com", password="test")

    def test_create_notification(self):
        notification = NotificationService.create_notification(
            recipient=self.user,
            title="Service Test",
            message="Content",
            notification_type=NotificationType.ALERT
        )
        self.assertEqual(notification.title, "Service Test")

    def test_get_user_notifications(self):
        Notification.objects.create(recipient=self.user, title="Notif 1")
        Notification.objects.create(recipient=self.user, title="Notif 2")
        notifications = NotificationService.get_user_notifications(self.user.id)
        self.assertEqual(notifications.count(), 2)

    def test_mark_as_read(self):
        notification = Notification.objects.create(recipient=self.user, title="Read Me", is_read=False)
        read = NotificationService.mark_as_read(notification)
        self.assertTrue(read.is_read)
        self.assertIsNotNone(read.read_at)

    def test_mark_all_as_read(self):
        Notification.objects.create(recipient=self.user, title="A", is_read=False)
        Notification.objects.create(recipient=self.user, title="B", is_read=False)
        count = NotificationService.mark_all_as_read(self.user.id)
        self.assertEqual(count, 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

    def test_get_unread_count(self):
        Notification.objects.create(recipient=self.user, title="A", is_read=False)
        Notification.objects.create(recipient=self.user, title="B", is_read=True)
        unread = NotificationService.get_unread_count(self.user.id)
        self.assertEqual(unread, 1)


class NotificationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="recipient3", email="rec3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "recipient_id": self.user.id,
            "title": "New Notification",
            "message": "Message",
            "notification_type": NotificationType.REMINDER,
            "channel": NotificationChannel.EMAIL
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        notification = serializer.save()
        self.assertEqual(notification.recipient, self.user)

    def test_update_serializer(self):
        notification = Notification.objects.create(recipient=self.user, title="Old", is_read=False)
        data = {"is_read": True}
        serializer = NotificationUpdateSerializer(notification, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_read)

    def test_display_serializer(self):
        notification = Notification.objects.create(recipient=self.user, title="Display")
        serializer = NotificationDisplaySerializer(notification)
        self.assertEqual(serializer.data["title"], "Display")
        self.assertEqual(serializer.data["recipient"]["id"], self.user.id)