from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.teacher import Teacher
from ...users.models import User
from ...common.enums.teachers import TeacherStatus, TeacherType, HighestDegree

class TeacherService:
    """Service for Teacher model operations"""

    @staticmethod
    def generate_teacher_id() -> str:
        import random
        import string
        year = date.today().year
        random_digits = ''.join(random.choices(string.digits, k=6))
        return f"TCH-{year}-{random_digits}"

    @staticmethod
    def create_teacher(
        user: User,
        first_name: str,
        last_name: str,
        birth_date: date,
        gender: str,
        hire_date: date,
        teacher_id: Optional[str] = None,
        middle_name: str = "",
        suffix: str = "",
        contact_number: str = "",
        personal_email: str = "",
        status: str = TeacherStatus.ACTIVE,
        teacher_type: str = TeacherType.FULL_TIME,
        highest_degree: str = "",
        years_of_experience: int = 0,
        profile_picture_url: str = ""
    ) -> Teacher:
        try:
            with transaction.atomic():
                teacher = Teacher(
                    user=user,
                    teacher_id=teacher_id or TeacherService.generate_teacher_id(),
                    first_name=first_name.title(),
                    middle_name=middle_name.title(),
                    last_name=last_name.title(),
                    suffix=suffix,
                    gender=gender,
                    birth_date=birth_date,
                    contact_number=contact_number,
                    personal_email=personal_email,
                    status=status,
                    teacher_type=teacher_type,
                    highest_degree=highest_degree,
                    hire_date=hire_date,
                    years_of_experience=years_of_experience,
                    profile_picture_url=profile_picture_url
                )
                teacher.full_clean()
                teacher.save()
                return teacher
        except ValidationError as e:
            raise

    @staticmethod
    def get_teacher_by_id(teacher_id: int) -> Optional[Teacher]:
        try:
            return Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return None

    @staticmethod
    def get_teacher_by_teacher_id(teacher_id_str: str) -> Optional[Teacher]:
        try:
            return Teacher.objects.get(teacher_id=teacher_id_str)
        except Teacher.DoesNotExist:
            return None

    @staticmethod
    def get_teacher_by_user(user_id: int) -> Optional[Teacher]:
        try:
            return Teacher.objects.get(user_id=user_id)
        except Teacher.DoesNotExist:
            return None

    @staticmethod
    def get_all_teachers(active_only: bool = True, limit: int = 100) -> List[Teacher]:
        queryset = Teacher.objects.all()
        if active_only:
            queryset = queryset.filter(status=TeacherStatus.ACTIVE)
        return queryset.order_by('last_name', 'first_name')[:limit]

    @staticmethod
    def update_teacher(teacher: Teacher, update_data: Dict[str, Any]) -> Teacher:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(teacher, field):
                        if field in ['first_name', 'middle_name', 'last_name']:
                            value = value.title()
                        setattr(teacher, field, value)
                teacher.full_clean()
                teacher.save()
                return teacher
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(teacher: Teacher, status: str) -> Teacher:
        teacher.status = status
        teacher.save()
        return teacher

    @staticmethod
    def delete_teacher(teacher: Teacher, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                teacher.is_active = False
                teacher.save()
            else:
                teacher.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_teachers(query: str, limit: int = 20) -> List[Teacher]:
        from django.db import models
        return Teacher.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(teacher_id__icontains=query) |
            models.Q(personal_email__icontains=query)
        )[:limit]

    @staticmethod
    def get_teachers_by_department(department_id: int) -> List[Teacher]:
        # Assuming department is linked via employee in HR, but for direct use in teaching assignments
        # This is a placeholder; actual implementation would use HR employee relationship
        from ...hr.models import Employee
        employees = Employee.objects.filter(department_id=department_id)
        user_ids = employees.values_list('user_id', flat=True)
        return Teacher.objects.filter(user_id__in=user_ids)