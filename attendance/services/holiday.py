from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.holiday import Holiday

class HolidayService:
    """Service for Holiday model operations"""

    @staticmethod
    def create_holiday(
        name: str,
        date: date,
        is_school_wide: bool = True,
        notes: str = ""
    ) -> Holiday:
        try:
            with transaction.atomic():
                holiday = Holiday(
                    name=name,
                    date=date,
                    is_school_wide=is_school_wide,
                    notes=notes
                )
                holiday.full_clean()
                holiday.save()
                return holiday
        except ValidationError as e:
            raise

    @staticmethod
    def get_holiday_by_id(holiday_id: int) -> Optional[Holiday]:
        try:
            return Holiday.objects.get(id=holiday_id)
        except Holiday.DoesNotExist:
            return None

    @staticmethod
    def get_holiday_by_date(date: date) -> Optional[Holiday]:
        try:
            return Holiday.objects.get(date=date)
        except Holiday.DoesNotExist:
            return None

    @staticmethod
    def get_all_holidays(year: Optional[int] = None) -> List[Holiday]:
        queryset = Holiday.objects.all()
        if year:
            queryset = queryset.filter(date__year=year)
        return queryset.order_by('date')

    @staticmethod
    def get_upcoming_holidays(days_ahead: int = 30) -> List[Holiday]:
        from django.utils import timezone
        today = timezone.now().date()
        end_date = today + timezone.timedelta(days=days_ahead)
        return Holiday.objects.filter(date__gte=today, date__lte=end_date).order_by('date')

    @staticmethod
    def update_holiday(holiday: Holiday, update_data: Dict[str, Any]) -> Holiday:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(holiday, field):
                        setattr(holiday, field, value)
                holiday.full_clean()
                holiday.save()
                return holiday
        except ValidationError as e:
            raise

    @staticmethod
    def delete_holiday(holiday: Holiday) -> bool:
        try:
            holiday.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def is_holiday(date: date, school_wide_only: bool = False) -> bool:
        """Check if a given date is a holiday"""
        queryset = Holiday.objects.filter(date=date)
        if school_wide_only:
            queryset = queryset.filter(is_school_wide=True)
        return queryset.exists()