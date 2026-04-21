from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional
from decimal import Decimal

from ..models.grade import AssessmentGrade
from ..models.submission import Submission

class AssessmentGradeService:
    """Service for AssessmentGrade model operations"""

    @staticmethod
    def create_or_update_grade(
        submission: Submission,
        raw_score: Decimal,
        percentage_score: Optional[Decimal] = None,
        transmuted_grade: Optional[Decimal] = None,
        remarks: str = ""
    ) -> AssessmentGrade:
        try:
            with transaction.atomic():
                grade, created = AssessmentGrade.objects.update_or_create(
                    submission=submission,
                    defaults={
                        'raw_score': raw_score,
                        'percentage_score': percentage_score,
                        'transmuted_grade': transmuted_grade,
                        'remarks': remarks
                    }
                )
                grade.full_clean()
                grade.save()
                return grade
        except ValidationError as e:
            raise

    @staticmethod
    def get_grade_by_submission(submission_id: int) -> Optional[AssessmentGrade]:
        try:
            return AssessmentGrade.objects.get(submission_id=submission_id)
        except AssessmentGrade.DoesNotExist:
            return None

    @staticmethod
    def calculate_percentage(raw_score: Decimal, total_points: Decimal) -> Decimal:
        if total_points == 0:
            return Decimal('0')
        return (raw_score / total_points) * 100

    @staticmethod
    def delete_grade(grade: AssessmentGrade) -> bool:
        try:
            grade.delete()
            return True
        except Exception:
            return False