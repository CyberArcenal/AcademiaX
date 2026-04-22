from django.test import TestCase
from django.utils import timezone
from users.models import User
from communication.models import Conversation, Message
from communication.services.message import MessageService
from communication.serializers.message import (
    MessageCreateSerializer,
    MessageUpdateSerializer,
    MessageDisplaySerializer,
)
from common.enums.communication import ConversationType, MessageStatus


class MessageModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="sender", email="sender@example.com", password="test")
        self.user2 = User.objects.create_user(username="receiver", email="receiver@example.com", password="test")
        self.conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user1
        )
        self.conversation.participants.add(self.user1, self.user2)

    def test_create_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello!",
            status=MessageStatus.SENT
        )
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Hello!")

    def test_str_method(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Test message"
        )
        expected = f"{self.user1}: Test message"
        self.assertEqual(str(message), expected)


class MessageServiceTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="sender2", email="sender2@example.com", password="test")
        self.user2 = User.objects.create_user(username="receiver2", email="receiver2@example.com", password="test")
        self.conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user1
        )
        self.conversation.participants.add(self.user1, self.user2)

    def test_send_message(self):
        message = MessageService.send_message(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello via service"
        )
        self.assertEqual(message.content, "Hello via service")
        self.assertEqual(message.status, MessageStatus.SENT)

    def test_get_conversation_messages(self):
        Message.objects.create(conversation=self.conversation, sender=self.user1, content="First")
        Message.objects.create(conversation=self.conversation, sender=self.user2, content="Second")
        messages = MessageService.get_conversation_messages(self.conversation.id)
        self.assertEqual(messages.count(), 2)

    def test_mark_as_delivered(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Deliver")
        delivered = MessageService.mark_as_delivered(message)
        self.assertEqual(delivered.status, MessageStatus.DELIVERED)
        self.assertIsNotNone(delivered.delivered_at)

    def test_mark_as_read(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Read")
        read = MessageService.mark_as_read(message)
        self.assertEqual(read.status, MessageStatus.READ)
        self.assertIsNotNone(read.read_at)

    def test_edit_message(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Original")
        edited = MessageService.edit_message(message, "Edited content")
        self.assertEqual(edited.content, "Edited content")
        self.assertTrue(edited.is_edited)
        self.assertIsNotNone(edited.edited_at)

    def test_delete_for_sender(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Delete")
        deleted = MessageService.delete_for_sender(message)
        self.assertTrue(deleted.is_deleted_for_sender)

    def test_delete_for_all(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Delete all")
        deleted = MessageService.delete_for_all(message)
        self.assertTrue(deleted.is_deleted_for_all)


class MessageSerializerTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="ser1", email="ser1@test.com", password="test")
        self.user2 = User.objects.create_user(username="ser2", email="ser2@test.com", password="test")
        self.conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user1
        )
        self.conversation.participants.add(self.user1, self.user2)

    def test_create_serializer_valid(self):
        data = {
            "conversation_id": self.conversation.id,
            "sender_id": self.user1.id,
            "content": "Test message"
        }
        serializer = MessageCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        message = serializer.save()
        self.assertEqual(message.conversation, self.conversation)

    def test_update_serializer_edit(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Old")
        data = {"content": "New content"}
        serializer = MessageUpdateSerializer(message, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.content, "New content")

    def test_update_serializer_delete_for_sender(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Old")
        data = {"is_deleted_for_sender": True}
        serializer = MessageUpdateSerializer(message, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(updated.is_deleted_for_sender)

    def test_display_serializer(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.user1, content="Display")
        serializer = MessageDisplaySerializer(message)
        self.assertEqual(serializer.data["content"], "Display")
        self.assertEqual(serializer.data["sender"]["id"], self.user1.id)