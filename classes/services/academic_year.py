from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.academic_year import AcademicYear

class AcademicYearService:
    """Service for AcademicYear model operations"""

    @staticmethod
    def create_academic_year(
        name: str,
        start_date: date,
        end_date: date,
        is_current: bool = False
    ) -> AcademicYear:
        try:
            with transaction.atomic():
                if is_current:
                    # Unset previous current academic year
                    AcademicYear.objects.filter(is_current=True).update(is_current=False)

                academic_year = AcademicYear(
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current
                )
                academic_year.full_clean()
                academic_year.save()
                return academic_year
        except ValidationError as e:
            raise

    @staticmethod
    def get_academic_year_by_id(year_id: int) -> Optional[AcademicYear]:
        try:
            return AcademicYear.objects.get(id=year_id)
        except AcademicYear.DoesNotExist:
            return None

    @staticmethod
    def get_academic_year_by_name(name: str) -> Optional[AcademicYear]:
        try:
            return AcademicYear.objects.get(name=name)
        except AcademicYear.DoesNotExist:
            return None

    @staticmethod
    def get_current_academic_year() -> Optional[AcademicYear]:
        try:
            return AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            return None

    @staticmethod
    def get_all_academic_years(include_inactive: bool = True) -> List[AcademicYear]:
        queryset = AcademicYear.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('-start_date')

    @staticmethod
    def update_academic_year(academic_year: AcademicYear, update_data: Dict[str, Any]) -> AcademicYear:
        try:
            with transaction.atomic():
                if update_data.get('is_current') and not academic_year.is_current:
                    # Unset others
                    AcademicYear.objects.filter(is_current=True).update(is_current=False)

                for field, value in update_data.items():
                    if hasattr(academic_year, field):
                        setattr(academic_year, field, value)
                academic_year.full_clean()
                academic_year.save()
                return academic_year
        except ValidationError as e:
            raise

    @staticmethod
    def delete_academic_year(academic_year: AcademicYear, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                academic_year.is_active = False
                academic_year.save()
            else:
                academic_year.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def set_current(academic_year: AcademicYear) -> AcademicYear:
        with transaction.atomic():
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
            academic_year.is_current = True
            academic_year.save()
            return academic_year