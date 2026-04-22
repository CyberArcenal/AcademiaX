from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from classes.models.academic_year import AcademicYear
from classes.models.term import Term



class TermService:
    """Service for Term model operations"""

    @staticmethod
    def create_term(
        academic_year: AcademicYear,
        term_type: str,
        term_number: int,
        name: str,
        start_date: date,
        end_date: date,
        is_active: bool = True
    ) -> Term:
        try:
            with transaction.atomic():
                term = Term(
                    academic_year=academic_year,
                    term_type=term_type,
                    term_number=term_number,
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=is_active
                )
                term.full_clean()
                term.save()
                return term
        except ValidationError as e:
            raise

    @staticmethod
    def get_term_by_id(term_id: int) -> Optional[Term]:
        try:
            return Term.objects.get(id=term_id)
        except Term.DoesNotExist:
            return None

    @staticmethod
    def get_terms_by_academic_year(academic_year_id: int, active_only: bool = True) -> List[Term]:
        queryset = Term.objects.filter(academic_year_id=academic_year_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('term_number')

    @staticmethod
    def get_current_term(academic_year_id: Optional[int] = None) -> Optional[Term]:
        queryset = Term.objects.filter(is_active=True)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        # Assuming the term with start_date <= today <= end_date is current
        today = date.today()
        return queryset.filter(start_date__lte=today, end_date__gte=today).first()

    @staticmethod
    def update_term(term: Term, update_data: Dict[str, Any]) -> Term:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(term, field):
                        setattr(term, field, value)
                term.full_clean()
                term.save()
                return term
        except ValidationError as e:
            raise

    @staticmethod
    def delete_term(term: Term, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                term.is_active = False
                term.save()
            else:
                term.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def activate_term(term: Term) -> Term:
        term.is_active = True
        term.save()
        return term

    @staticmethod
    def deactivate_term(term: Term) -> Term:
        term.is_active = False
        term.save()
        return term