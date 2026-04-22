from django.test import TestCase
from django.utils import timezone
from users.models import BlacklistedAccessToken, User
from users.services.blacklisted_token import BlacklistedAccessTokenService


class BlacklistedAccessTokenModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")

    def test_blacklist_token(self):
        jti = "test-jti"
        expires_at = timezone.now() + timezone.timedelta(days=1)
        token, created = BlacklistedAccessToken.blacklist_token(jti, self.user, expires_at)
        self.assertTrue(created)
        self.assertEqual(token.jti, jti)

    def test_is_blacklisted(self):
        jti = "blacklisted"
        expires_at = timezone.now() + timezone.timedelta(days=1)
        BlacklistedAccessToken.blacklist_token(jti, self.user, expires_at)
        self.assertTrue(BlacklistedAccessToken.is_blacklisted(jti))
        self.assertFalse(BlacklistedAccessToken.is_blacklisted("nonexistent"))

    def test_cleanup_expired(self):
        expired_at = timezone.now() - timezone.timedelta(days=1)
        BlacklistedAccessToken.objects.create(jti="expired", user=self.user, expires_at=expired_at)
        future = timezone.now() + timezone.timedelta(days=1)
        BlacklistedAccessToken.objects.create(jti="future", user=self.user, expires_at=future)
        BlacklistedAccessToken.cleanup_expired()
        self.assertFalse(BlacklistedAccessToken.objects.filter(jti="expired").exists())
        self.assertTrue(BlacklistedAccessToken.objects.filter(jti="future").exists())