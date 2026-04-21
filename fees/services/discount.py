from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date

from ..models.discount import Discount
from ...classes.models.academic_year import AcademicYear
from ...classes.models.grade_level import GradeLevel
from ...common.enums.fees import DiscountType, FeeCategory

class DiscountService:
    """Service for Discount model operations"""

    @staticmethod
    def create_discount(
        name: str,
        discount_type: str,
        value: Decimal,
        is_percentage: bool = True,
        applicable_to: str = 'TUITION',
        specific_category: Optional[str] = None,
        academic_year: Optional[AcademicYear] = None,
        grade_level: Optional[GradeLevel] = None,
        is_active: bool = True,
        valid_until: Optional[date] = None
    ) -> Discount:
        try:
            with transaction.atomic():
                discount = Discount(
                    name=name,
                    discount_type=discount_type,
                    value=value,
                    is_percentage=is_percentage,
                    applicable_to=applicable_to,
                    specific_category=specific_category,
                    academic_year=academic_year,
                    grade_level=grade_level,
                    is_active=is_active,
                    valid_until=valid_until
                )
                discount.full_clean()
                discount.save()
                return discount
        except ValidationError as e:
            raise

    @staticmethod
    def get_discount_by_id(discount_id: int) -> Optional[Discount]:
        try:
            return Discount.objects.get(id=discount_id)
        except Discount.DoesNotExist:
            return None

    @staticmethod
    def get_active_discounts(academic_year_id: Optional[int] = None, grade_level_id: Optional[int] = None) -> List[Discount]:
        queryset = Discount.objects.filter(is_active=True)
        today = date.today()
        queryset = queryset.filter(valid_until__gte=today)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if grade_level_id:
            queryset = queryset.filter(grade_level_id=grade_level_id)
        return queryset

    @staticmethod
    def update_discount(discount: Discount, update_data: Dict[str, Any]) -> Discount:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(discount, field):
                        setattr(discount, field, value)
                discount.full_clean()
                discount.save()
                return discount
        except ValidationError as e:
            raise

    @staticmethod
    def delete_discount(discount: Discount, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                discount.is_active = False
                discount.save()
            else:
                discount.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def apply_discount(original_amount: Decimal, discount: Discount) -> Decimal:
        if discount.is_percentage:
            return original_amount * (discount.value / Decimal('100'))
        else:
            return min(discount.value, original_amount)