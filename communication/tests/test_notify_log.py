from django.test import TestCase
from django.utils import timezone
from communication.models import NotifyLog
from common.enums.communication import NotificationType


class NotifyLogModelTest(TestCase):
    def test_create_notify_log_minimal(self):
        log = NotifyLog.objects.create(
            recipient_email="user@example.com",
            type=NotificationType.INFO
        )
        self.assertEqual(log.recipient_email, "user@example.com")
        self.assertEqual(log.type, NotificationType.INFO)
        self.assertEqual(log.status, "queued")
        self.assertEqual(log.channel, "email")
        self.assertEqual(log.priority, "normal")
        self.assertEqual(log.retry_count, 0)
        self.assertEqual(log.resend_count, 0)

    def test_create_notify_log_full(self):
        log = NotifyLog.objects.create(
            recipient_email="full@example.com",
            subject="Test Subject",
            payload='{"key": "value"}',
            type=NotificationType.ALERT,
            status="sent",
            error_message="",
            channel="sms",
            priority="high",
            message_id="msg_123",
            duration_ms=150,
            retry_count=2,
            resend_count=1,
            metadata={"source": "api"}
        )
        self.assertEqual(log.subject, "Test Subject")
        self.assertEqual(log.payload, '{"key": "value"}')
        self.assertEqual(log.status, "sent")
        self.assertEqual(log.channel, "sms")
        self.assertEqual(log.message_id, "msg_123")
        self.assertEqual(log.duration_ms, 150)

    def test_status_choices_accepts_valid(self):
        valid_statuses = ["queued", "sent", "failed", "resend"]
        for status in valid_statuses:
            log = NotifyLog.objects.create(
                recipient_email=f"{status}@example.com",
                status=status
            )
            self.assertEqual(log.status, status)

    def test_invalid_status_raises_integrity_error(self):
        with self.assertRaises(Exception):
            NotifyLog.objects.create(
                recipient_email="invalid@example.com",
                status="invalid_status"
            )

    def test_str_method(self):
        log = NotifyLog.objects.create(
            recipient_email="str@example.com",
            status="failed"
        )
        expected = "str@example.com - failed"
        self.assertEqual(str(log), expected)

    def test_auto_timestamps(self):
        log = NotifyLog.objects.create(
            recipient_email="time@example.com"
        )
        self.assertIsNotNone(log.created_at)
        self.assertIsNotNone(log.updated_at)
        old_updated = log.updated_at
        log.status = "sent"
        log.save()
        log.refresh_from_db()
        self.assertGreater(log.updated_at, old_updated)

    def test_sent_at_can_be_set_manually(self):
        now = timezone.now()
        log = NotifyLog.objects.create(
            recipient_email="sent@example.com",
            sent_at=now
        )
        self.assertEqual(log.sent_at, now)

    def test_last_error_at_can_be_set(self):
        now = timezone.now()
        log = NotifyLog.objects.create(
            recipient_email="error@example.com",
            last_error_at=now
        )
        self.assertEqual(log.last_error_at, now)

    def test_meta_indexes(self):
        # Verify indexes are defined (not a functional test)
        indexes = NotifyLog._meta.indexes
        index_names = [idx.name for idx in indexes]
        self.assertIn("idx_notify_status", index_names)
        self.assertIn("idx_notify_recipient", index_names)
        self.assertIn("idx_notify_status_created", index_names)

    def test_ordering(self):
        log1 = NotifyLog.objects.create(
            recipient_email="a@example.com",
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        log2 = NotifyLog.objects.create(
            recipient_email="b@example.com",
            created_at=timezone.now()
        )
        logs = NotifyLog.objects.all()
        self.assertEqual(logs.first(), log2)  # most recent first
        self.assertEqual(logs.last(), log1)

    def test_retry_count_increments_manually(self):
        log = NotifyLog.objects.create(
            recipient_email="retry@example.com",
            retry_count=0
        )
        log.retry_count += 1
        log.save()
        log.refresh_from_db()
        self.assertEqual(log.retry_count, 1)