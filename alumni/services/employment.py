from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.employment import Employment
from ..models.alumni import Alumni
from ...common.enums.alumni import EmploymentType

class EmploymentService:
    """Service for Employment model operations"""

    @staticmethod
    def create_employment(
        alumni: Alumni,
        job_title: str,
        company_name: str,
        start_date: date,
        employment_type: str = EmploymentType.FULL_TIME,
        end_date: Optional[date] = None,
        is_current: bool = False,
        location: str = "",
        industry: str = ""
    ) -> Employment:
        try:
            with transaction.atomic():
                # If setting is_current=True, unset previous current
                if is_current:
                    Employment.objects.filter(alumni=alumni, is_current=True).update(is_current=False)

                employment = Employment(
                    alumni=alumni,
                    job_title=job_title.title(),
                    company_name=company_name.title(),
                    employment_type=employment_type,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current,
                    location=location,
                    industry=industry
                )
                employment.full_clean()
                employment.save()
                return employment
        except ValidationError as e:
            raise

    @staticmethod
    def get_employment_by_id(employment_id: int) -> Optional[Employment]:
        try:
            return Employment.objects.get(id=employment_id)
        except Employment.DoesNotExist:
            return None

    @staticmethod
    def get_employments_by_alumni(alumni_id: int) -> List[Employment]:
        return Employment.objects.filter(alumni_id=alumni_id).order_by('-start_date')

    @staticmethod
    def get_current_employment(alumni_id: int) -> Optional[Employment]:
        try:
            return Employment.objects.get(alumni_id=alumni_id, is_current=True)
        except Employment.DoesNotExist:
            return None

    @staticmethod
    def update_employment(employment: Employment, update_data: Dict[str, Any]) -> Employment:
        try:
            with transaction.atomic():
                if update_data.get('is_current') and not employment.is_current:
                    # Unset others
                    Employment.objects.filter(alumni=employment.alumni, is_current=True).update(is_current=False)

                for field, value in update_data.items():
                    if hasattr(employment, field):
                        if field in ['job_title', 'company_name']:
                            value = value.title()
                        setattr(employment, field, value)
                employment.full_clean()
                employment.save()
                return employment
        except ValidationError as e:
            raise

    @staticmethod
    def delete_employment(employment: Employment) -> bool:
        try:
            employment.delete()
            return True
        except Exception:
            return False