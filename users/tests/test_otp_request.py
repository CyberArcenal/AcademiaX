from django.test import TestCase
from django.utils import timezone
from users.models import OtpRequest, User
from users.services.otp_request import OtpRequestService
from users.enums.otp_request import OtpRequestType
from rest_framework.validators import ValidationError

class OtpRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="otp_user", password="pass")

    def test_create_otp_request(self):
        otp = OtpRequest.objects.create(
            user=self.user,
            otp_code="123456",
            email="test@example.com",
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            type=OtpRequestType.EMAIL
        )
        self.assertEqual(otp.user, self.user)
        self.assertEqual(otp.otp_code, "123456")
        self.assertEqual(otp.type, OtpRequestType.EMAIL)

    def test_clean_requires_email_or_phone(self):
        with self.assertRaises(ValidationError):
            otp = OtpRequest(user=self.user, otp_code="123456", expires_at=timezone.now() + timezone.timedelta(minutes=5))
            otp.full_clean()

    def test_str_method(self):
        otp = OtpRequest.objects.create(
            user=self.user,
            otp_code="654321",
            email="str@example.com",
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        expected = f"OTP for {self.user.username} - 654321"
        self.assertEqual(str(otp), expected)


class OtpRequestServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="otp_svc", password="pass")

    def test_generate_otp(self):
        otp = OtpRequestService.generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_create_otp(self):
        otp = OtpRequestService.create_otp(
            user=self.user,
            otp_type=OtpRequestType.EMAIL,
            email="svc@example.com"
        )
        self.assertIsNotNone(otp.otp_code)
        self.assertEqual(otp.type, OtpRequestType.EMAIL)
        self.assertFalse(otp.is_used)

    def test_verify_otp_correct(self):
        otp = OtpRequest.objects.create(
            user=self.user,
            otp_code="999999",
            email="verify@example.com",
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            type=OtpRequestType.EMAIL,
            is_used=False
        )
        result = OtpRequestService.verify_otp(self.user, "999999", OtpRequestType.EMAIL)
        self.assertTrue(result)
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_verify_otp_wrong_code(self):
        OtpRequest.objects.create(
            user=self.user,
            otp_code="111111",
            email="wrong@example.com",
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            type=OtpRequestType.EMAIL
        )
        result = OtpRequestService.verify_otp(self.user, "222222", OtpRequestType.EMAIL)
        self.assertFalse(result)

    def test_increment_attempt(self):
        otp = OtpRequest.objects.create(
            user=self.user,
            otp_code="123456",
            email="attempt@example.com",
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        count = OtpRequestService.increment_attempt(otp)
        self.assertEqual(count, 1)
        otp.refresh_from_db()
        self.assertEqual(otp.attempt_count, 1)