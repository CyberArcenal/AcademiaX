from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from assessments.models.question import Question
from assessments.models.assessment import Assessment
from common.enums.assessment import QuestionType

class QuestionService:
    """Service for Question model operations"""

    @staticmethod
    def create_question(
        assessment: Assessment,
        question_text: str,
        question_type: str,
        points: float = 1.0,
        order: int = 0,
        explanation: str = "",
        is_required: bool = True
    ) -> Question:
        try:
            with transaction.atomic():
                question = Question(
                    assessment=assessment,
                    question_text=question_text,
                    question_type=question_type,
                    points=points,
                    order=order,
                    explanation=explanation,
                    is_required=is_required
                )
                question.full_clean()
                question.save()
                return question
        except ValidationError as e:
            raise

    @staticmethod
    def get_question_by_id(question_id: int) -> Optional[Question]:
        try:
            return Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return None

    @staticmethod
    def get_questions_by_assessment(assessment_id: int) -> List[Question]:
        return Question.objects.filter(assessment_id=assessment_id).order_by('order')

    @staticmethod
    def update_question(question: Question, update_data: Dict[str, Any]) -> Question:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(question, field):
                        setattr(question, field, value)
                question.full_clean()
                question.save()
                return question
        except ValidationError as e:
            raise

    @staticmethod
    def delete_question(question: Question) -> bool:
        try:
            question.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def reorder_questions(assessment_id: int, question_ids_in_order: List[int]) -> bool:
        try:
            with transaction.atomic():
                for idx, qid in enumerate(question_ids_in_order, start=1):
                    Question.objects.filter(id=qid, assessment_id=assessment_id).update(order=idx)
            return True
        except Exception:
            return False