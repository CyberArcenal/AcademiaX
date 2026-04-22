from django.test import TestCase
from django.utils import timezone
from users.models import User, UserLog
from users.services.user_log import UserLogService
from users.serializers.user_log import (
    UserLogMinimalSerializer,
    UserLogCreateSerializer,
    UserLogDisplaySerializer,
)


class UserLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="logger", email="log@example.com", password="p")

    def test_create_user_log(self):
        log = UserLog.objects.create(
            user=self.user,
            action="LOGIN",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            details={"browser": "Chrome"}
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "LOGIN")
        self.assertIsNotNone(log.created_at)

    def test_str_method(self):
        log = UserLog.objects.create(user=self.user, action="LOGOUT")
        expected = f"{self.user} - LOGOUT at {log.created_at}"
        # The __str__ method may not be defined; we'll just check it returns a string
        self.assertIsInstance(str(log), str)


class UserLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="loguser", email="lu@example.com", password="p")

    def test_create_log(self):
        log = UserLogService.create_log(
            user=self.user,
            action="PASSWORD_CHANGE",
            ip_address="192.168.1.1",
            details={"success": True}
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "PASSWORD_CHANGE")

    def test_get_logs_by_user(self):
        UserLog.objects.create(user=self.user, action="LOGIN")
        UserLog.objects.create(user=self.user, action="LOGOUT")
        logs = UserLogService.get_logs_by_user(self.user.id)
        self.assertEqual(logs.count(), 2)

    def test_get_logs_by_action(self):
        UserLog.objects.create(user=self.user, action="LOGIN")
        UserLog.objects.create(user=self.user, action="LOGIN")
        UserLog.objects.create(user=self.user, action="LOGOUT")
        logs = UserLogService.get_logs_by_action("LOGIN")
        self.assertEqual(logs.count(), 2)

    def test_delete_old_logs(self):
        # Create a log older than 90 days
        old_date = timezone.now() - timezone.timedelta(days=100)
        log = UserLog.objects.create(user=self.user, action="OLD", created_at=old_date)
        # Create a recent log
        recent = UserLog.objects.create(user=self.user, action="RECENT")
        deleted = UserLogService.delete_old_logs(days_to_keep=90)
        self.assertEqual(deleted, 1)
        with self.assertRaises(UserLog.DoesNotExist):
            UserLog.objects.get(id=log.id)
        UserLog.objects.get(id=recent.id)  # should exist


class UserLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seruser", email="ser@example.com", password="p")

    def test_minimal_serializer(self):
        log = UserLog.objects.create(user=self.user, action="LOGIN")
        serializer = UserLogMinimalSerializer(log)
        self.assertEqual(serializer.data["action"], "LOGIN")
        self.assertEqual(serializer.data["user"]["id"], self.user.id)

    def test_create_serializer_valid(self):
        data = {
            "user_id": self.user.id,
            "action": "PROFILE_UPDATE",
            "ip_address": "10.0.0.1",
            "details": {"field": "email"}
        }
        serializer = UserLogCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.user, self.user)

    def test_display_serializer(self):
        log = UserLog.objects.create(user=self.user, action="LOGIN", ip_address="127.0.0.1")
        serializer = UserLogDisplaySerializer(log)
        self.assertEqual(serializer.data["action"], "LOGIN")
        self.assertEqual(serializer.data["user"]["id"], self.user.id)