from django.test import TestCase
from django.utils import timezone
from users.models import User
from parents.models import Parent, ParentCommunicationLog
from parents.services.parent_communication import ParentCommunicationLogService
from parents.serializers.parent_communication import (
    ParentCommunicationLogCreateSerializer,
    ParentCommunicationLogUpdateSerializer,
    ParentCommunicationLogDisplaySerializer,
)


class ParentCommunicationLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", email="staff@example.com", password="test")
        self.parent_user = User.objects.create_user(username="parent1", email="p1@example.com", password="test")
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_create_communication_log(self):
        log = ParentCommunicationLog.objects.create(
            parent=self.parent,
            subject="Meeting Reminder",
            message="Parent-teacher meeting on Friday",
            channel="EMAIL",
            direction="OUTGOING",
            sent_by=self.user,
            follow_up_required=False
        )
        self.assertEqual(log.parent, self.parent)
        self.assertEqual(log.subject, "Meeting Reminder")
        self.assertEqual(log.channel, "EMAIL")

    def test_str_method(self):
        log = ParentCommunicationLog.objects.create(parent=self.parent, subject="Test", channel="SMS", direction="INCOMING")
        expected = f"Communication with {self.parent} - Test"
        self.assertEqual(str(log), expected)


class ParentCommunicationLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff2", email="staff2@example.com", password="test")
        self.parent_user = User.objects.create_user(username="parent2", email="p2@example.com", password="test")
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_create_log(self):
        log = ParentCommunicationLogService.create_log(
            parent=self.parent,
            subject="Fee Reminder",
            message="Tuition fee due on 15th",
            channel="EMAIL",
            direction="OUTGOING",
            sent_by=self.user,
            follow_up_required=True
        )
        self.assertEqual(log.parent, self.parent)
        self.assertTrue(log.follow_up_required)

    def test_get_logs_by_parent(self):
        ParentCommunicationLog.objects.create(parent=self.parent, subject="Log1", channel="CALL", direction="INCOMING")
        ParentCommunicationLog.objects.create(parent=self.parent, subject="Log2", channel="SMS", direction="OUTGOING")
        logs = ParentCommunicationLogService.get_logs_by_parent(self.parent.id)
        self.assertEqual(logs.count(), 2)

    def test_resolve_log(self):
        log = ParentCommunicationLog.objects.create(parent=self.parent, subject="Issue", is_resolved=False)
        resolved = ParentCommunicationLogService.resolve_log(log, self.user, "Resolved by staff")
        self.assertTrue(resolved.is_resolved)
        self.assertIsNotNone(resolved.resolved_at)
        self.assertEqual(resolved.resolved_by, self.user)


class ParentCommunicationLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff3", email="staff3@example.com", password="test")
        self.parent_user = User.objects.create_user(username="parent3", email="p3@example.com", password="test")
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_create_serializer_valid(self):
        data = {
            "parent_id": self.parent.id,
            "subject": "Report Card",
            "message": "Report card is ready",
            "channel": "EMAIL",
            "direction": "OUTGOING",
            "sent_by_id": self.user.id
        }
        serializer = ParentCommunicationLogCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.parent, self.parent)

    def test_update_serializer_resolve(self):
        log = ParentCommunicationLog.objects.create(parent=self.parent, subject="Pending", is_resolved=False)
        data = {"is_resolved": True, "resolved_by_id": self.user.id}
        serializer = ParentCommunicationLogUpdateSerializer(log, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_resolved)

    def test_display_serializer(self):
        log = ParentCommunicationLog.objects.create(parent=self.parent, subject="Display", channel="SMS", direction="INCOMING")
        serializer = ParentCommunicationLogDisplaySerializer(log)
        self.assertEqual(serializer.data["subject"], "Display")
        self.assertEqual(serializer.data["parent"]["id"], self.parent.id)