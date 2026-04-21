from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import models
from typing import Optional, List, Dict, Any

from ..models.alumni import Alumni
from ...students.models.student import Student
from ...users.models import User

class AlumniService:
    """Service for Alumni model operations"""

    @staticmethod
    def create_alumni(
        graduation_year: int,
        student: Optional[Student] = None,
        user: Optional[User] = None,
        batch: str = "",
        current_city: str = "",
        current_country: str = "Philippines",
        contact_number: str = "",
        personal_email: str = "",
        facebook_url: str = "",
        linkedin_url: str = "",
        is_active: bool = True,
        **extra_fields
    ) -> Alumni:
        """Create a new alumni record"""
        try:
            with transaction.atomic():
                alumni = Alumni(
                    student=student,
                    user=user,
                    graduation_year=graduation_year,
                    batch=batch,
                    current_city=current_city,
                    current_country=current_country,
                    contact_number=contact_number,
                    personal_email=personal_email,
                    facebook_url=facebook_url,
                    linkedin_url=linkedin_url,
                    is_active=is_active,
                    **extra_fields
                )
                alumni.full_clean()
                alumni.save()
                return alumni
        except ValidationError as e:
            raise
        except Exception as e:
            raise ValidationError(str(e))

    @staticmethod
    def get_alumni_by_id(alumni_id: int) -> Optional[Alumni]:
        try:
            return Alumni.objects.get(id=alumni_id)
        except Alumni.DoesNotExist:
            return None

    @staticmethod
    def get_alumni_by_student(student_id: int) -> Optional[Alumni]:
        try:
            return Alumni.objects.get(student_id=student_id)
        except Alumni.DoesNotExist:
            return None

    @staticmethod
    def get_alumni_by_user(user_id: int) -> Optional[Alumni]:
        try:
            return Alumni.objects.get(user_id=user_id)
        except Alumni.DoesNotExist:
            return None

    @staticmethod
    def get_all_alumni(active_only: bool = True, limit: int = 100) -> List[Alumni]:
        queryset = Alumni.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset[:limit]

    @staticmethod
    def update_alumni(alumni: Alumni, update_data: Dict[str, Any]) -> Alumni:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(alumni, field):
                        setattr(alumni, field, value)
                alumni.full_clean()
                alumni.save()
                return alumni
        except ValidationError as e:
            raise

    @staticmethod
    def delete_alumni(alumni: Alumni, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                alumni.is_active = False
                alumni.save()
            else:
                alumni.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_alumni(query: str, limit: int = 20) -> List[Alumni]:
        return Alumni.objects.filter(
            models.Q(student__first_name__icontains=query) |
            models.Q(student__last_name__icontains=query) |
            models.Q(user__first_name__icontains=query) |
            models.Q(user__last_name__icontains=query) |
            models.Q(batch__icontains=query) |
            models.Q(current_city__icontains=query)
        )[:limit]

    @staticmethod
    def get_alumni_by_graduation_year(year: int) -> List[Alumni]:
        return Alumni.objects.filter(graduation_year=year, is_active=True)

    @staticmethod
    def get_alumni_by_batch(batch: str) -> List[Alumni]:
        return Alumni.objects.filter(batch=batch, is_active=True)