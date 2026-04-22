from django.test import TestCase
from django.utils import timezone
from users.models import User
from communication.models import Announcement, BroadcastLog
from communication.services.broadcast_log import BroadcastLogService
from communication.serializers.broadcast_log import (
    BroadcastLogCreateSerializer,
    BroadcastLogUpdateSerializer,
    BroadcastLogDisplaySerializer,
)
from common.enums.communication import TargetAudience, NotificationChannel


class BroadcastLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")
        self.announcement = Announcement.objects.create(
            title="Test Announcement",
            content="Content",
            author=self.user,
            target_audience=TargetAudience.ALL,
            is_published=True
        )
        self.recipient = User.objects.create_user(username="recipient", email="rec@example.com", password="test")

    def test_create_broadcast_log(self):
        log = BroadcastLog.objects.create(
            announcement=self.announcement,
            recipient=self.recipient,
            channel="APP",
            status="PENDING"
        )
        self.assertEqual(log.announcement, self.announcement)
        self.assertEqual(log.recipient, self.recipient)
        self.assertEqual(log.status, "PENDING")

    def test_str_method(self):
        log = BroadcastLog.objects.create(
            announcement=self.announcement,
            recipient=self.recipient,
            channel="EMAIL"
        )
        expected = f"{self.announcement.title} -> {self.recipient} (EMAIL)"
        self.assertEqual(str(log), expected)


class BroadcastLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")
        self.announcement = Announcement.objects.create(
            title="Test",
            content="Content",
            author=self.user,
            is_published=True
        )
        self.recipient = User.objects.create_user(username="rec2", email="rec2@example.com", password="test")

    def test_create_log(self):
        log = BroadcastLogService.create_log(
            announcement=self.announcement,
            recipient=self.recipient,
            channel="SMS",
            status="PENDING"
        )
        self.assertEqual(log.channel, "SMS")

    def test_get_logs_by_announcement(self):
        BroadcastLog.objects.create(announcement=self.announcement, recipient=self.recipient, channel="APP")
        logs = BroadcastLogService.get_logs_by_announcement(self.announcement.id)
        self.assertEqual(logs.count(), 1)

    def test_update_status(self):
        log = BroadcastLog.objects.create(announcement=self.announcement, recipient=self.recipient, channel="APP", status="PENDING")
        updated = BroadcastLogService.update_status(log, "SENT")
        self.assertEqual(updated.status, "SENT")
        self.assertIsNotNone(updated.sent_at)

    def test_get_failed_logs(self):
        BroadcastLog.objects.create(announcement=self.announcement, recipient=self.recipient, channel="APP", status="FAILED")
        failed = BroadcastLogService.get_failed_logs()
        self.assertEqual(failed.count(), 1)

    def test_retry_failed(self):
        log = BroadcastLog.objects.create(announcement=self.announcement, recipient=self.recipient, channel="APP", status="FAILED", error_message="Error")
        retried = BroadcastLogService.retry_failed(log)
        self.assertEqual(retried.status, "PENDING")
        self.assertEqual(retried.error_message, "")


class BroadcastLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", email="admin3@example.com", password="test")
        self.announcement = Announcement.objects.create(
            title="Test",
            content="Content",
            author=self.user,
            is_published=True
        )
        self.recipient = User.objects.create_user(username="rec3", email="rec3@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "announcement_id": self.announcement.id,
            "recipient_id": self.recipient.id,
            "channel": "APP",
            "status": "PENDING"
        }
        serializer = BroadcastLogCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.announcement, self.announcement)

    def test_update_serializer(self):
        log = BroadcastLog.objects.create(announcement=self.announcement, recipient=self.recipient, channel="APP", status="PENDING")
        data = {"status": "SENT"}
        serializer = BroadcastLogUpdateSerializer(log, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, "SENT")

    def test_display_serializer(self):
        log = BroadcastLog.objects.create(announcement=self.announcement, recipient=self.recipient, channel="EMAIL", status="PENDING")
        serializer = BroadcastLogDisplaySerializer(log)
        self.assertEqual(serializer.data["announcement"]["id"], self.announcement.id)
        self.assertEqual(serializer.data["recipient"]["id"], self.recipient.id)
        self.assertEqual(serializer.data["channel"], "EMAIL")