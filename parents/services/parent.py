from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.parent import Parent
from users.models import User
from common.enums.parents import ParentStatus

class ParentService:
    """Service for Parent model operations"""

    @staticmethod
    def create_parent(
        user: User,
        status: str = ParentStatus.ACTIVE,
        contact_number: str = "",
        alternative_contact: str = "",
        email: str = "",
        occupation: str = "",
        employer: str = "",
        employer_address: str = "",
        emergency_contact_name: str = "",
        emergency_contact_number: str = "",
        preferred_language: str = "English",
        receive_notifications: bool = True,
        receive_email_digest: bool = True
    ) -> Parent:
        try:
            with transaction.atomic():
                parent = Parent(
                    user=user,
                    status=status,
                    contact_number=contact_number,
                    alternative_contact=alternative_contact,
                    email=email,
                    occupation=occupation,
                    employer=employer,
                    employer_address=employer_address,
                    emergency_contact_name=emergency_contact_name,
                    emergency_contact_number=emergency_contact_number,
                    preferred_language=preferred_language,
                    receive_notifications=receive_notifications,
                    receive_email_digest=receive_email_digest
                )
                parent.full_clean()
                parent.save()
                return parent
        except ValidationError as e:
            raise

    @staticmethod
    def get_parent_by_id(parent_id: int) -> Optional[Parent]:
        try:
            return Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return None

    @staticmethod
    def get_parent_by_user(user_id: int) -> Optional[Parent]:
        try:
            return Parent.objects.get(user_id=user_id)
        except Parent.DoesNotExist:
            return None

    @staticmethod
    def get_all_parents(active_only: bool = True, limit: int = 100) -> List[Parent]:
        queryset = Parent.objects.all()
        if active_only:
            queryset = queryset.filter(status=ParentStatus.ACTIVE)
        return queryset.select_related('user')[:limit]

    @staticmethod
    def update_parent(parent: Parent, update_data: Dict[str, Any]) -> Parent:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(parent, field):
                        setattr(parent, field, value)
                parent.full_clean()
                parent.save()
                return parent
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(parent: Parent, status: str) -> Parent:
        parent.status = status
        parent.save()
        return parent

    @staticmethod
    def delete_parent(parent: Parent, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                parent.is_active = False
                parent.save()
            else:
                parent.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_parents(query: str, limit: int = 20) -> List[Parent]:
        from django.db import models
        return Parent.objects.filter(
            models.Q(user__first_name__icontains=query) |
            models.Q(user__last_name__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(contact_number__icontains=query)
        ).select_related('user')[:limit]