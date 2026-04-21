from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from django.db import models

from common.enums.users import AccountStatus, UserRole
from users.models.user import User

class UserService:
    """Service for User model operations"""

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        role: str = UserRole.STUDENT,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: str = "",
        suffix: str = "",
        phone_number: str = "",
        is_active: bool = True,
        status: str = AccountStatus.ACTIVE,
        **extra_fields,
    ) -> User:
        """Create a new user with hashed password"""
        try:
            with transaction.atomic():
                user = User(
                    username=str(username),
                    email=email,
                    role=role,
                    first_name=str(first_name).title() if first_name else "",
                    last_name=str(last_name).title() if last_name else "",
                    middle_name=middle_name.title(),
                    suffix=suffix,
                    phone_number=phone_number,
                    is_active=is_active,
                    status=status,
                    **extra_fields,
                )
                user.set_password(password)
                user.full_clean()
                user.save()

                # Create default security settings if needed
                # from .user_security_settings import UserSecuritySettingsService
                # UserSecuritySettingsService.create_default_settings(user)

                return user
        except IntegrityError as e:
            if "username" in str(e).lower():
                raise ValidationError(f"Username '{username}' already exists")
            elif "email" in str(e).lower():
                raise ValidationError(f"Email '{email}' already exists")
            raise
        except ValidationError as e:
            raise

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_all_users(active_only: bool = True, limit: int = 100) -> List[User]:
        queryset = User.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset[:limit]

    @staticmethod
    def get_users_by_role(role: str, active_only: bool = True) -> List[User]:
        queryset = User.objects.filter(role=role)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def update_user(user: User, update_data: Dict[str, Any]) -> User:
        """Update user information"""
        try:
            with transaction.atomic():
                # Handle password separately
                if "password" in update_data:
                    user.set_password(update_data.pop("password"))

                # Update other fields
                for field, value in update_data.items():
                    if hasattr(user, field):
                        if field in ['first_name', 'last_name', 'middle_name']:
                            value = value.title()
                        setattr(user, field, value)

                user.full_clean()
                user.save()
                return user
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(user: User, status: str) -> User:
        user.status = status
        user.save()
        return user

    @staticmethod
    def deactivate_user(user: User) -> User:
        user.status = AccountStatus.RESTRICTED
        user.is_active = False
        user.save()

        # Logout all sessions - implement if login session exists
        # from .login_session import LoginSessionService
        # LoginSessionService.deactivate_all_user_sessions(user)

        return user

    @staticmethod
    def activate_user(user: User) -> User:
        user.status = AccountStatus.ACTIVE
        user.is_active = True
        user.save()
        return user

    @staticmethod
    def change_password(user: User, new_password: str) -> User:
        user.set_password(new_password)
        user.save()
        return user

    @staticmethod
    def delete_user(user: User, soft_delete: bool = True) -> bool:
        try:
            with transaction.atomic():
                if soft_delete:
                    user.status = AccountStatus.DELETED
                    user.is_active = False
                    user.save()

                    # Anonymize sensitive data
                    user.email = f"deleted_{user.id}@deleted.com"
                    user.username = f"deleted_{user.id}"
                    user.first_name = "Deleted"
                    user.last_name = "User"
                    user.middle_name = ""
                    user.phone_number = ""
                    user.save()

                    # Deactivate all sessions
                    # from .login_session import LoginSessionService
                    # LoginSessionService.deactivate_all_user_sessions(user)
                else:
                    user.delete()
                return True
        except Exception:
            return False

    @staticmethod
    def search_users(query: str, limit: int = 20) -> List[User]:
        return User.objects.filter(
            models.Q(username__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(phone_number__icontains=query)
        )[:limit]

    @staticmethod
    def verify_user(user: User) -> User:
        user.is_verified = True
        user.save()
        return user

    @staticmethod
    def get_user_count_by_role() -> Dict[str, int]:
        from django.db.models import Count
        return dict(User.objects.values_list('role').annotate(count=Count('id')))