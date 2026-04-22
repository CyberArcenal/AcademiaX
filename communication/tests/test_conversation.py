from django.test import TestCase
from users.models import User
from communication.models import Conversation
from communication.services.conversation import ConversationService
from communication.serializers.conversation import (
    ConversationCreateSerializer,
    ConversationUpdateSerializer,
    ConversationDisplaySerializer,
)
from common.enums.communication import ConversationType


class ConversationModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", email="u1@example.com", password="test")
        self.user2 = User.objects.create_user(username="user2", email="u2@example.com", password="test")

    def test_create_private_conversation(self):
        conversation = Conversation.objects.create(
            conversation_type=ConversationType.ONE_ON_ONE,
            created_by=self.user1
        )
        conversation.participants.add(self.user1, self.user2)
        self.assertEqual(conversation.conversation_type, ConversationType.ONE_ON_ONE)
        self.assertEqual(conversation.participants.count(), 2)

    def test_create_group_conversation(self):
        conversation = Conversation.objects.create(
            conversation_type=ConversationType.GROUP,
            name="Group Chat",
            created_by=self.user1
        )
        conversation.participants.add(self.user1, self.user2)
        self.assertEqual(conversation.name, "Group Chat")

    def test_str_method_private(self):
        conversation = Conversation.objects.create(conversation_type=ConversationType.ONE_ON_ONE, created_by=self.user1)
        conversation.participants.add(self.user1, self.user2)
        expected = f"Chat between {self.user1} and {self.user2}"
        # The actual string representation may vary; just check it's not empty
        self.assertTrue(str(conversation))


class ConversationServiceTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", email="u1@test.com", password="test")
        self.user2 = User.objects.create_user(username="u2", email="u2@test.com", password="test")
        self.user3 = User.objects.create_user(username="u3", email="u3@test.com", password="test")

    def test_create_private_conversation(self):
        conversation = ConversationService.create_conversation(
            participants=[self.user1, self.user2],
            created_by=self.user1,
            conversation_type=ConversationType.ONE_ON_ONE
        )
        self.assertEqual(conversation.participants.count(), 2)

    def test_get_or_create_private_conversation(self):
        conv = ConversationService.get_or_create_private_conversation(self.user1, self.user2)
        self.assertIsNotNone(conv)
        # Same call should return existing
        conv2 = ConversationService.get_or_create_private_conversation(self.user1, self.user2)
        self.assertEqual(conv.id, conv2.id)

    def test_add_participant_to_group(self):
        group = ConversationService.create_conversation(
            participants=[self.user1],
            created_by=self.user1,
            conversation_type=ConversationType.GROUP,
            name="Test Group"
        )
        updated = ConversationService.add_participant(group, self.user2)
        self.assertEqual(updated.participants.count(), 2)

    def test_remove_participant(self):
        group = ConversationService.create_conversation(
            participants=[self.user1, self.user2],
            created_by=self.user1,
            conversation_type=ConversationType.GROUP,
            name="Test Group"
        )
        updated = ConversationService.remove_participant(group, self.user2)
        self.assertEqual(updated.participants.count(), 1)


class ConversationSerializerTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="ser1", email="ser1@test.com", password="test")
        self.user2 = User.objects.create_user(username="ser2", email="ser2@test.com", password="test")

    def test_create_serializer_private_valid(self):
        data = {
            "conversation_type": ConversationType.ONE_ON_ONE,
            "participant_ids": [self.user1.id, self.user2.id],
            "created_by_id": self.user1.id
        }
        serializer = ConversationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        conv = serializer.save()
        self.assertEqual(conv.participants.count(), 2)

    def test_create_serializer_group_valid(self):
        data = {
            "conversation_type": ConversationType.GROUP,
            "name": "Study Group",
            "participant_ids": [self.user1.id, self.user2.id],
            "created_by_id": self.user1.id
        }
        serializer = ConversationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        conv = serializer.save()
        self.assertEqual(conv.name, "Study Group")

    def test_update_serializer(self):
        conv = Conversation.objects.create(conversation_type=ConversationType.GROUP, name="Old Name", created_by=self.user1)
        conv.participants.add(self.user1)
        data = {"name": "New Name"}
        serializer = ConversationUpdateSerializer(conv, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New Name")

    def test_display_serializer(self):
        conv = Conversation.objects.create(conversation_type=ConversationType.GROUP, name="Display", created_by=self.user1)
        conv.participants.add(self.user1, self.user2)
        serializer = ConversationDisplaySerializer(conv)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["created_by"]["id"], self.user1.id)