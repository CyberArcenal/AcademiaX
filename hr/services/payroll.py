from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, timezone

from ..models.payroll import SalaryGrade, PayrollPeriod

class SalaryGradeService:
    """Service for SalaryGrade model operations"""

    @staticmethod
    def create_salary_grade(
        grade: int,
        basic_salary: Decimal,
        hourly_rate: Optional[Decimal] = None,
        description: str = ""
    ) -> SalaryGrade:
        try:
            with transaction.atomic():
                salary_grade = SalaryGrade(
                    grade=grade,
                    basic_salary=basic_salary,
                    hourly_rate=hourly_rate,
                    description=description
                )
                salary_grade.full_clean()
                salary_grade.save()
                return salary_grade
        except ValidationError as e:
            raise

    @staticmethod
    def get_salary_grade_by_id(grade_id: int) -> Optional[SalaryGrade]:
        try:
            return SalaryGrade.objects.get(id=grade_id)
        except SalaryGrade.DoesNotExist:
            return None

    @staticmethod
    def get_salary_grade_by_level(grade: int) -> Optional[SalaryGrade]:
        try:
            return SalaryGrade.objects.get(grade=grade)
        except SalaryGrade.DoesNotExist:
            return None

    @staticmethod
    def update_salary_grade(salary_grade: SalaryGrade, update_data: Dict[str, Any]) -> SalaryGrade:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(salary_grade, field):
                        setattr(salary_grade, field, value)
                salary_grade.full_clean()
                salary_grade.save()
                return salary_grade
        except ValidationError as e:
            raise

    @staticmethod
    def delete_salary_grade(salary_grade: SalaryGrade) -> bool:
        try:
            salary_grade.delete()
            return True
        except Exception:
            return False


class PayrollPeriodService:
    """Service for PayrollPeriod model operations"""

    @staticmethod
    def create_payroll_period(
        name: str,
        start_date: date,
        end_date: date,
        is_closed: bool = False
    ) -> PayrollPeriod:
        try:
            with transaction.atomic():
                period = PayrollPeriod(
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_closed=is_closed
                )
                period.full_clean()
                period.save()
                return period
        except ValidationError as e:
            raise

    @staticmethod
    def get_payroll_period_by_id(period_id: int) -> Optional[PayrollPeriod]:
        try:
            return PayrollPeriod.objects.get(id=period_id)
        except PayrollPeriod.DoesNotExist:
            return None

    @staticmethod
    def get_current_payroll_period() -> Optional[PayrollPeriod]:
        today = date.today()
        return PayrollPeriod.objects.filter(start_date__lte=today, end_date__gte=today, is_closed=False).first()

    @staticmethod
    def update_payroll_period(period: PayrollPeriod, update_data: Dict[str, Any]) -> PayrollPeriod:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(period, field):
                        setattr(period, field, value)
                period.full_clean()
                period.save()
                return period
        except ValidationError as e:
            raise

    @staticmethod
    def close_period(period: PayrollPeriod) -> PayrollPeriod:
        period.is_closed = True
        period.closed_at = timezone.now()
        period.save()
        return period

    @staticmethod
    def delete_payroll_period(period: PayrollPeriod) -> bool:
        try:
            period.delete()
            return True
        except Exception:
            return False