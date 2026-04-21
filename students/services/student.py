from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.student import Student
from ...users.models import User
from ...common.enums.students import StudentStatus, Gender

class StudentService:
    """Service for Student model operations"""

    @staticmethod
    def generate_student_id() -> str:
        import random
        import string
        year = date.today().year
        random_digits = ''.join(random.choices(string.digits, k=6))
        return f"{year}-{random_digits}"

    @staticmethod
    def create_student(
        first_name: str,
        last_name: str,
        birth_date: date,
        gender: str,
        student_id: Optional[str] = None,
        user: Optional[User] = None,
        middle_name: str = "",
        suffix: str = "",
        lrn: str = "",
        birth_place: str = "",
        nationality: str = "Filipino",
        religion: str = "",
        current_address: str = "",
        permanent_address: str = "",
        contact_number: str = "",
        personal_email: str = "",
        status: str = StudentStatus.ACTIVE,
        profile_picture_url: str = ""
    ) -> Student:
        try:
            with transaction.atomic():
                student = Student(
                    user=user,
                    student_id=student_id or StudentService.generate_student_id(),
                    lrn=lrn,
                    first_name=first_name.title(),
                    middle_name=middle_name.title(),
                    last_name=last_name.title(),
                    suffix=suffix,
                    gender=gender,
                    birth_date=birth_date,
                    birth_place=birth_place,
                    nationality=nationality,
                    religion=religion,
                    current_address=current_address,
                    permanent_address=permanent_address or current_address,
                    contact_number=contact_number,
                    personal_email=personal_email,
                    status=status,
                    profile_picture_url=profile_picture_url
                )
                student.full_clean()
                student.save()
                return student
        except ValidationError as e:
            raise

    @staticmethod
    def get_student_by_id(student_id: int) -> Optional[Student]:
        try:
            return Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return None

    @staticmethod
    def get_student_by_student_id(student_id: str) -> Optional[Student]:
        try:
            return Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            return None

    @staticmethod
    def get_student_by_user(user_id: int) -> Optional[Student]:
        try:
            return Student.objects.get(user_id=user_id)
        except Student.DoesNotExist:
            return None

    @staticmethod
    def get_all_students(active_only: bool = True, limit: int = 100) -> List[Student]:
        queryset = Student.objects.all()
        if active_only:
            queryset = queryset.filter(status=StudentStatus.ACTIVE)
        return queryset.order_by('last_name', 'first_name')[:limit]

    @staticmethod
    def update_student(student: Student, update_data: Dict[str, Any]) -> Student:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(student, field):
                        if field in ['first_name', 'middle_name', 'last_name']:
                            value = value.title()
                        setattr(student, field, value)
                student.full_clean()
                student.save()
                return student
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(student: Student, status: str) -> Student:
        student.status = status
        student.save()
        return student

    @staticmethod
    def delete_student(student: Student, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                student.is_active = False
                student.save()
            else:
                student.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_students(query: str, limit: int = 20) -> List[Student]:
        from django.db import models
        return Student.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(student_id__icontains=query) |
            models.Q(lrn__icontains=query)
        )[:limit]

    @staticmethod
    def get_students_by_grade_level(grade_level_id: int, academic_year_id: int) -> List[Student]:
        from ...enrollments.models import Enrollment
        enrollments = Enrollment.objects.filter(
            grade_level_id=grade_level_id,
            academic_year_id=academic_year_id,
            status='ENR'
        ).select_related('student')
        return [e.student for e in enrollments]