from django.test import TestCase
from django.utils import timezone
from users.models import LoginSession, User
from users.services.login_session import LoginSessionService


class LoginSessionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="session_user", password="pass")
        self.expires_at = timezone.now() + timezone.timedelta(days=7)

    def test_create_session(self):
        session = LoginSession.objects.create(
            user=self.user,
            device_name="Chrome on Windows",
            user_agent="Mozilla/5.0",
            ip_address="127.0.0.1",
            refresh_token="refresh123",
            access_token="access123",
            expires_at=self.expires_at,
            is_active=True
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.device_name, "Chrome on Windows")
        self.assertTrue(session.is_active)

    def test_is_valid_property(self):
        session = LoginSession.objects.create(
            user=self.user,
            device_name="Test",
            ip_address="0.0.0.0",
            refresh_token="r1",
            expires_at=timezone.now() + timezone.timedelta(hours=1),
            is_active=True
        )
        self.assertTrue(session.is_valid)
        session.is_active = False
        self.assertFalse(session.is_valid)
        session.is_active = True
        session.expires_at = timezone.now() - timezone.timedelta(hours=1)
        self.assertFalse(session.is_valid)

    def test_str_method(self):
        session = LoginSession.objects.create(
            user=self.user,
            device_name="Firefox",
            ip_address="0.0.0.0",
            refresh_token="r2",
            expires_at=self.expires_at
        )
        expected = f"{self.user.username} - Firefox"
        self.assertEqual(str(session), expected)


class LoginSessionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="svc_user", password="pass")
        self.expires_at = timezone.now() + timezone.timedelta(days=7)

    def test_create_session(self):
        session = LoginSessionService.create_session(
            user=self.user,
            device_name="Safari on Mac",
            user_agent="Safari",
            ip_address="192.168.1.1",
            refresh_token="rtoken",
            access_token="atoken",
            expires_at=self.expires_at
        )
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)

    def test_get_active_sessions(self):
        LoginSession.objects.create(
            user=self.user, device_name="Active1", ip_address="1.1.1.1",
            refresh_token="r1", expires_at=timezone.now() + timezone.timedelta(days=1), is_active=True
        )
        LoginSession.objects.create(
            user=self.user, device_name="Inactive", ip_address="2.2.2.2",
            refresh_token="r2", expires_at=timezone.now() + timezone.timedelta(days=1), is_active=False
        )
        active = LoginSessionService.get_active_sessions(self.user)
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().device_name, "Active1")

    def test_deactivate_all_user_sessions(self):
        LoginSession.objects.create(
            user=self.user, device_name="D1", ip_address="1.1.1.1",
            refresh_token="r1", expires_at=self.expires_at, is_active=True
        )
        LoginSession.objects.create(
            user=self.user, device_name="D2", ip_address="2.2.2.2",
            refresh_token="r2", expires_at=self.expires_at, is_active=True
        )
        LoginSessionService.deactivate_all_user_sessions(self.user)
        self.assertEqual(LoginSession.objects.filter(user=self.user, is_active=True).count(), 0)

    def test_get_session_by_refresh_token(self):
        created = LoginSession.objects.create(
            user=self.user, device_name="Test", ip_address="0.0.0.0",
            refresh_token="unique_refresh", expires_at=self.expires_at
        )
        fetched = LoginSessionService.get_session_by_refresh_token("unique_refresh")
        self.assertEqual(fetched, created)
        self.assertIsNone(LoginSessionService.get_session_by_refresh_token("nonexistent"))