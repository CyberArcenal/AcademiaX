from django.test import TestCase
from django.utils import timezone
from users.models import LoginCheckpoint, User
from users.services.login_checkpoint import LoginCheckpointService


class LoginCheckpointTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="pass")

    def test_create_checkpoint(self):
        checkpoint = LoginCheckpointService.create_checkpoint(user=self.user)
        self.assertIsNotNone(checkpoint.token)
        self.assertFalse(checkpoint.is_used)
        self.assertGreater(checkpoint.expires_at, timezone.now())

    def test_is_valid(self):
        checkpoint = LoginCheckpointService.create_checkpoint(user=self.user, expires_at=timezone.now() + timezone.timedelta(minutes=5))
        self.assertTrue(checkpoint.is_valid)
        checkpoint.is_used = True
        self.assertFalse(checkpoint.is_valid)

    def test_use_checkpoint(self):
        checkpoint = LoginCheckpointService.create_checkpoint(user=self.user)
        self.assertTrue(LoginCheckpointService.use_checkpoint(checkpoint))
        self.assertTrue(checkpoint.is_used)
        # Second use should fail
        self.assertFalse(LoginCheckpointService.use_checkpoint(checkpoint))