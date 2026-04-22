from django.test import TestCase
from users.models import UserSecuritySettings, User
from users.services.user_security_settings import UserSecuritySettingsService


class UserSecuritySettingsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="settings_user", password="pass")

    def test_create_settings(self):
        settings = UserSecuritySettings.objects.create(
            user=self.user,
            two_factor_enabled=False,
            recovery_email="backup@example.com",
            alert_on_new_device=True
        )
        self.assertEqual(settings.user, self.user)
        self.assertFalse(settings.two_factor_enabled)
        self.assertEqual(settings.recovery_email, "backup@example.com")

    def test_soft_delete(self):
        settings = UserSecuritySettings.objects.create(user=self.user)
        settings.delete()
        self.assertTrue(settings.is_deleted)

    def test_str_method(self):
        settings = UserSecuritySettings.objects.create(user=self.user)
        expected = f"Security settings for {self.user.username}"
        self.assertEqual(str(settings), expected)


class UserSecuritySettingsServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="settings_svc", password="pass")

    def test_get_or_create_settings(self):
        settings = UserSecuritySettingsService.get_or_create_settings(self.user)
        self.assertIsNotNone(settings)
        # Second call returns same
        settings2 = UserSecuritySettingsService.get_or_create_settings(self.user)
        self.assertEqual(settings.id, settings2.id)

    def test_enable_two_factor(self):
        settings = UserSecuritySettingsService.enable_two_factor(self.user)
        self.assertTrue(settings.two_factor_enabled)

    def test_disable_two_factor(self):
        settings = UserSecuritySettingsService.enable_two_factor(self.user)
        self.assertTrue(settings.two_factor_enabled)
        settings2 = UserSecuritySettingsService.disable_two_factor(self.user)
        self.assertFalse(settings2.two_factor_enabled)

    def test_update_recovery_contacts(self):
        settings = UserSecuritySettingsService.update_recovery_contacts(
            self.user, recovery_email="new@example.com", recovery_phone="09123456789"
        )
        self.assertEqual(settings.recovery_email, "new@example.com")
        self.assertEqual(settings.recovery_phone, "09123456789")