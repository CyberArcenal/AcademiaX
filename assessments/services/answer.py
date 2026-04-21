from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.answer import Answer
from ..models.submission import Submission
from ..models.question import Question
from ..models.choice import Choice

class AnswerService:
    """Service for Answer model operations"""

    @staticmethod
    def create_or_update_answer(
        submission: Submission,
        question: Question,
        selected_choice: Optional[Choice] = None,
        text_answer: str = "",
        matching_answer: Optional[Dict] = None,
        points_earned: Optional[float] = None,
        feedback: str = ""
    ) -> Answer:
        try:
            with transaction.atomic():
                answer, created = Answer.objects.update_or_create(
                    submission=submission,
                    question=question,
                    defaults={
                        'selected_choice': selected_choice,
                        'text_answer': text_answer,
                        'matching_answer': matching_answer,
                        'points_earned': points_earned,
                        'feedback': feedback
                    }
                )
                answer.full_clean()
                answer.save()
                return answer
        except ValidationError as e:
            raise

    @staticmethod
    def get_answer_by_id(answer_id: int) -> Optional[Answer]:
        try:
            return Answer.objects.get(id=answer_id)
        except Answer.DoesNotExist:
            return None

    @staticmethod
    def get_answers_by_submission(submission_id: int) -> List[Answer]:
        return Answer.objects.filter(submission_id=submission_id).select_related('question')

    @staticmethod
    def grade_answer(answer: Answer, points_earned: float, feedback: str = "") -> Answer:
        answer.points_earned = points_earned
        answer.feedback = feedback
        answer.save()
        return answer

    @staticmethod
    def delete_answer(answer: Answer) -> bool:
        try:
            answer.delete()
            return True
        except Exception:
            return False