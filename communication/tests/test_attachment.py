from django.test import TestCase
from users.models import User
from communication.models import Conversation, Message, MessageAttachment
from communication.services.attachment import MessageAttachmentService
from communication.serializers.attachment import (
    MessageAttachmentCreateSerializer,
    MessageAttachmentUpdateSerializer,
    MessageAttachmentDisplaySerializer,
)
from common.enums.communication import ConversationType


class MessageAttachmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sender", email="sender@example.com", password="test")
        self.recipient = User.objects.create_user(username="receiver", email="receiver@example.com", password="test")
        self.conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user
        )
        self.conversation.participants.add(self.user, self.recipient)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="With attachment"
        )

    def test_create_attachment(self):
        attachment = MessageAttachment.objects.create(
            message=self.message,
            file_url="http://example.com/file.pdf",
            file_name="document.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=self.user
        )
        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.file_name, "document.pdf")
        self.assertEqual(attachment.file_size, 1024)

    def test_str_method(self):
        attachment = MessageAttachment.objects.create(
            message=self.message,
            file_name="test.jpg",
            file_url="http://example.com/test.jpg",
            uploaded_by=self.user
        )
        self.assertEqual(str(attachment), "test.jpg")


class MessageAttachmentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sender2", email="sender2@example.com", password="test")
        self.recipient = User.objects.create_user(username="receiver2", email="receiver2@example.com", password="test")
        self.conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user
        )
        self.conversation.participants.add(self.user, self.recipient)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="With attachment"
        )

    def test_create_attachment(self):
        attachment = MessageAttachmentService.create_attachment(
            message=self.message,
            file_url="http://example.com/doc.pdf",
            file_name="doc.pdf",
            file_size=2048,
            mime_type="application/pdf",
            uploaded_by=self.user
        )
        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.file_name, "doc.pdf")

    def test_get_attachments_by_message(self):
        MessageAttachment.objects.create(message=self.message, file_name="a.pdf", file_url="http://a", uploaded_by=self.user)
        MessageAttachment.objects.create(message=self.message, file_name="b.pdf", file_url="http://b", uploaded_by=self.user)
        attachments = MessageAttachmentService.get_attachments_by_message(self.message.id)
        self.assertEqual(attachments.count(), 2)

    def test_delete_attachment(self):
        attachment = MessageAttachment.objects.create(message=self.message, file_name="del.pdf", file_url="http://del", uploaded_by=self.user)
        success = MessageAttachmentService.delete_attachment(attachment)
        self.assertTrue(success)
        with self.assertRaises(MessageAttachment.DoesNotExist):
            MessageAttachment.objects.get(id=attachment.id)


class MessageAttachmentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ser1", email="ser1@test.com", password="test")
        self.recipient = User.objects.create_user(username="ser2", email="ser2@test.com", password="test")
        self.conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user
        )
        self.conversation.participants.add(self.user, self.recipient)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Attachment test"
        )

    def test_create_serializer_valid(self):
        data = {
            "message_id": self.message.id,
            "file_url": "http://example.com/image.png",
            "file_name": "image.png",
            "file_size": 512,
            "mime_type": "image/png",
            "uploaded_by_id": self.user.id
        }
        serializer = MessageAttachmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        attachment = serializer.save()
        self.assertEqual(attachment.message, self.message)

    def test_update_serializer(self):
        attachment = MessageAttachment.objects.create(
            message=self.message, file_name="old.jpg", file_url="http://old", uploaded_by=self.user
        )
        # Update is not really supported, but the serializer exists
        data = {}  # No fields to update
        serializer = MessageAttachmentUpdateSerializer(attachment, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.file_name, "old.jpg")

    def test_display_serializer(self):
        attachment = MessageAttachment.objects.create(
            message=self.message, file_name="display.pdf", file_url="http://display", uploaded_by=self.user
        )
        serializer = MessageAttachmentDisplaySerializer(attachment)
        self.assertEqual(serializer.data["file_name"], "display.pdf")
        self.assertEqual(serializer.data["message"]["id"], self.message.id)