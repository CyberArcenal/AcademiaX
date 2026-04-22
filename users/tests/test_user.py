from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from common.enums.users import AccountStatus, UserRole
from users.models import UserLog
from users.services.user import UserService
from users.services.user_log import UserLogService
from users.serializers.user import (
    UserMinimalSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserDisplaySerializer,
)
from users.serializers.user_log import (
    UserLogMinimalSerializer,
    UserLogCreateSerializer,
    UserLogDisplaySerializer,
)

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user_minimal(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=UserRole.STUDENT
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertEqual(user.status, AccountStatus.ACTIVE)
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            role=UserRole.ADMIN
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_str_method(self):
        user = User.objects.create_user(username="juan", first_name="Juan", last_name="Dela Cruz")
        self.assertEqual(str(user), "juan")

    def test_get_full_name(self):
        user = User.objects.create_user(
            username="maria",
            first_name="Maria",
            last_name="Santos",
            middle_name="Cruz",
            suffix="Jr."
        )
        self.assertEqual(user.get_full_name(), "Maria Cruz Santos Jr.")

    def test_role_choices(self):
        for role in [UserRole.ADMIN, UserRole.REGISTRAR, UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT, UserRole.STAFF, UserRole.ACCOUNTING]:
            user = User.objects.create_user(username=f"user_{role}", email=f"{role}@example.com", password="pass", role=role)
            self.assertEqual(user.role, role)


class UserServiceTest(TestCase):
    def test_create_user(self):
        user = UserService.create_user(
            username="jose",
            email="jose@example.com",
            password="secure123",
            first_name="Jose",
            last_name="Rizal",
            role=UserRole.TEACHER
        )
        self.assertEqual(user.username, "jose")
        self.assertEqual(user.role, UserRole.TEACHER)
        self.assertTrue(user.check_password("secure123"))

    def test_get_user_by_username(self):
        created = User.objects.create_user(username="unique", email="u@example.com", password="p")
        fetched = UserService.get_user_by_username("unique")
        self.assertEqual(fetched, created)

    def test_update_user(self):
        user = User.objects.create_user(username="update", email="up@example.com", password="old")
        updated = UserService.update_user(user, {"first_name": "Updated", "phone_number": "09123456789"})
        self.assertEqual(updated.first_name, "Updated")

    def test_deactivate_user(self):
        user = User.objects.create_user(username="active", email="active@example.com", password="p", status=AccountStatus.ACTIVE, is_active=True)
        deactivated = UserService.deactivate_user(user)
        self.assertEqual(deactivated.status, AccountStatus.RESTRICTED)
        self.assertFalse(deactivated.is_active)

    def test_delete_user_soft(self):
        user = User.objects.create_user(username="todelete", email="del@example.com", password="p")
        success = UserService.delete_user(user, soft_delete=True)
        self.assertTrue(success)
        user.refresh_from_db()
        self.assertEqual(user.status, AccountStatus.DELETED)
        self.assertFalse(user.is_active)
        self.assertTrue(user.username.startswith("deleted_"))

    def test_search_users(self):
        User.objects.create_user(username="john_doe", email="john@example.com", first_name="John")
        User.objects.create_user(username="jane_doe", email="jane@example.com", first_name="Jane")
        results = UserService.search_users("john")
        self.assertEqual(results.count(), 1)


class UserSerializerTest(TestCase):
    def test_minimal_serializer(self):
        user = User.objects.create_user(username="minimal", email="min@example.com", password="p", first_name="Min", last_name="User")
        serializer = UserMinimalSerializer(user)
        self.assertEqual(serializer.data["username"], "minimal")
        self.assertEqual(serializer.data["first_name"], "Min")

    def test_create_serializer_valid(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123",
            "first_name": "New",
            "last_name": "User",
            "role": UserRole.STUDENT
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertTrue(user.check_password("strongpass123"))

    def test_create_serializer_invalid_missing_username(self):
        data = {"email": "no@example.com", "password": "pass"}
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)

    def test_update_serializer(self):
        user = User.objects.create_user(username="update_test", email="upd@example.com", password="old")
        data = {"first_name": "Updated", "phone_number": "12345"}
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.first_name, "Updated")

    def test_display_serializer(self):
        user = User.objects.create_user(username="display", email="disp@example.com", password="p", role=UserRole.ADMIN)
        serializer = UserDisplaySerializer(user)
        self.assertEqual(serializer.data["username"], "display")
        self.assertEqual(serializer.data["role"], UserRole.ADMIN)