from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date
from fees.models.discount import Discount
from fees.models.scholarship import Scholarship
from students.models.student import Student
from users.models import User

class ScholarshipService:
    """Service for Scholarship model operations"""

    @staticmethod
    def create_scholarship(
        student: Student,
        discount: Discount,
        scholarship_type: str,
        awarded_date: date,
        expiry_date: Optional[date] = None,
        is_renewable: bool = False,
        grantor: str = "",
        terms: str = "",
        approved_by: Optional[User] = None
    ) -> Scholarship:
        try:
            with transaction.atomic():
                scholarship = Scholarship(
                    student=student,
                    discount=discount,
                    scholarship_type=scholarship_type,
                    awarded_date=awarded_date,
                    expiry_date=expiry_date,
                    is_renewable=is_renewable,
                    grantor=grantor,
                    terms=terms,
                    approved_by=approved_by
                )
                scholarship.full_clean()
                scholarship.save()
                return scholarship
        except ValidationError as e:
            raise

    @staticmethod
    def get_scholarship_by_id(scholarship_id: int) -> Optional[Scholarship]:
        try:
            return Scholarship.objects.get(id=scholarship_id)
        except Scholarship.DoesNotExist:
            return None

    @staticmethod
    def get_scholarships_by_student(student_id: int, active_only: bool = True) -> List[Scholarship]:
        queryset = Scholarship.objects.filter(student_id=student_id)
        if active_only:
            queryset = queryset.filter(expiry_date__gte=date.today())
        return queryset

    @staticmethod
    def update_scholarship(scholarship: Scholarship, update_data: Dict[str, Any]) -> Scholarship:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(scholarship, field):
                        setattr(scholarship, field, value)
                scholarship.full_clean()
                scholarship.save()
                return scholarship
        except ValidationError as e:
            raise

    @staticmethod
    def renew_scholarship(scholarship: Scholarship, new_expiry_date: date) -> Scholarship:
        scholarship.expiry_date = new_expiry_date
        scholarship.save()
        return scholarship

    @staticmethod
    def delete_scholarship(scholarship: Scholarship) -> bool:
        try:
            scholarship.delete()
            return True
        except Exception:
            return False