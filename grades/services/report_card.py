from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.report_card import ReportCard
from ...students.models.student import Student
from ...classes.models.academic_year import AcademicYear
from ...classes.models.term import Term
from ...users.models import User

class ReportCardService:
    """Service for ReportCard model operations"""

    @staticmethod
    def create_report_card(
        student: Student,
        academic_year: AcademicYear,
        term: Term,
        gpa: Optional[Decimal] = None,
        total_units_earned: Decimal = Decimal('0'),
        honors: str = "",
        signed_by: Optional[User] = None,
        notes: str = ""
    ) -> ReportCard:
        try:
            with transaction.atomic():
                existing = ReportCard.objects.filter(
                    student=student,
                    academic_year=academic_year,
                    term=term
                ).first()
                if existing:
                    raise ValidationError("Report card already exists for this student, year, and term")

                report = ReportCard(
                    student=student,
                    academic_year=academic_year,
                    term=term,
                    gpa=gpa,
                    total_units_earned=total_units_earned,
                    honors=honors,
                    signed_by=signed_by,
                    notes=notes
                )
                report.full_clean()
                report.save()
                return report
        except ValidationError as e:
            raise

    @staticmethod
    def get_report_card_by_id(report_id: int) -> Optional[ReportCard]:
        try:
            return ReportCard.objects.get(id=report_id)
        except ReportCard.DoesNotExist:
            return None

    @staticmethod
    def get_report_card_by_student_term(student_id: int, academic_year_id: int, term_id: int) -> Optional[ReportCard]:
        try:
            return ReportCard.objects.get(
                student_id=student_id,
                academic_year_id=academic_year_id,
                term_id=term_id
            )
        except ReportCard.DoesNotExist:
            return None

    @staticmethod
    def get_report_cards_by_student(student_id: int) -> List[ReportCard]:
        return ReportCard.objects.filter(student_id=student_id).order_by('-academic_year__start_date')

    @staticmethod
    def update_report_card(report: ReportCard, update_data: Dict[str, Any]) -> ReportCard:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(report, field):
                        setattr(report, field, value)
                report.full_clean()
                report.save()
                return report
        except ValidationError as e:
            raise

    @staticmethod
    def compute_gpa_from_grades(student_id: int, academic_year_id: int, term_id: int) -> Decimal:
        from .grade import GradeService
        grades = GradeService.get_grades_by_student(student_id, term_id)
        if not grades:
            return Decimal('0')
        total_points = sum((g.percentage or 0) for g in grades)
        return total_points / len(grades)

    @staticmethod
    def delete_report_card(report: ReportCard) -> bool:
        try:
            report.delete()
            return True
        except Exception:
            return False