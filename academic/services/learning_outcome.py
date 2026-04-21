from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.learning_outcome import LearningOutcome
from ..models.subject import Subject

class LearningOutcomeService:
    """Service for LearningOutcome model operations"""

    @staticmethod
    def create_outcome(
        subject: Subject,
        code: str,
        description: str,
        order: int
    ) -> LearningOutcome:
        try:
            with transaction.atomic():
                outcome = LearningOutcome(
                    subject=subject,
                    code=code.upper(),
                    description=description,
                    order=order
                )
                outcome.full_clean()
                outcome.save()
                return outcome
        except ValidationError as e:
            raise

    @staticmethod
    def get_outcome_by_id(outcome_id: int) -> Optional[LearningOutcome]:
        try:
            return LearningOutcome.objects.get(id=outcome_id)
        except LearningOutcome.DoesNotExist:
            return None

    @staticmethod
    def get_outcomes_by_subject(subject_id: int) -> List[LearningOutcome]:
        return LearningOutcome.objects.filter(subject_id=subject_id).order_by('order')

    @staticmethod
    def update_outcome(outcome: LearningOutcome, update_data: Dict[str, Any]) -> LearningOutcome:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(outcome, field):
                        if field == 'code':
                            value = value.upper()
                        setattr(outcome, field, value)
                outcome.full_clean()
                outcome.save()
                return outcome
        except ValidationError as e:
            raise

    @staticmethod
    def delete_outcome(outcome: LearningOutcome) -> bool:
        try:
            outcome.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def reorder_outcomes(subject_id: int, outcome_ids_in_order: List[int]) -> bool:
        try:
            with transaction.atomic():
                for idx, outcome_id in enumerate(outcome_ids_in_order, start=1):
                    LearningOutcome.objects.filter(id=outcome_id, subject_id=subject_id).update(order=idx)
            return True
        except Exception:
            return False