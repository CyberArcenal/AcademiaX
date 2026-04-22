from django.test import TestCase
from django.utils import timezone
from users.models import SecurityLog, User
from users.services.security_log import SecurityLogService
from common.enums.security import SecurityEventType


class SecurityLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="log_user", password="pass")

    def test_create_security_log(self):
        log = SecurityLog.objects.create(
            user=self.user,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            details="Login from new device"
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.event_type, SecurityEventType.LOGIN_SUCCESS)

    def test_soft_delete(self):
        log = SecurityLog.objects.create(user=self.user, event_type=SecurityEventType.LOGOUT)
        log.delete()
        self.assertTrue(log.is_deleted)
        # The object still exists in the database
        self.assertIsNotNone(SecurityLog.objects.get(id=log.id))

    def test_str_method(self):
        log = SecurityLog.objects.create(user=self.user, event_type=SecurityEventType.PASSWORD_CHANGE)
        self.assertIn(self.user.username, str(log))


class SecurityLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="log_svc", password="pass")

    def test_create_log(self):
        log = SecurityLogService.create_log(
            user=self.user,
            event_type=SecurityEventType.TWO_FACTOR_ENABLED,
            ip_address="10.0.0.1",
            details="2FA enabled by user"
        )
        self.assertEqual(log.event_type, SecurityEventType.TWO_FACTOR_ENABLED)

    def test_get_logs_for_user(self):
        SecurityLog.objects.create(user=self.user, event_type=SecurityEventType.LOGIN_SUCCESS)
        SecurityLog.objects.create(user=self.user, event_type=SecurityEventType.LOGOUT)
        logs = SecurityLogService.get_logs_for_user(self.user)
        self.assertEqual(logs.count(), 2)

    def test_delete_old_logs(self):
        old = SecurityLog.objects.create(
            user=self.user,
            event_type=SecurityEventType.LOGIN_FAILED,
            created_at=timezone.now() - timezone.timedelta(days=100)
        )
        recent = SecurityLog.objects.create(
            user=self.user,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            created_at=timezone.now()
        )
        deleted = SecurityLogService.delete_old_logs(days=90)
        self.assertEqual(deleted, 1)
        old.refresh_from_db()
        self.assertTrue(old.is_deleted)
        recent.refresh_from_db()
        self.assertFalse(recent.is_deleted)