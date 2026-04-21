from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.choice import Choice
from ..models.question import Question

class ChoiceService:
    """Service for Choice model operations"""

    @staticmethod
    def create_choice(
        question: Question,
        choice_text: str,
        is_correct: bool = False,
        order: int = 0
    ) -> Choice:
        try:
            with transaction.atomic():
                choice = Choice(
                    question=question,
                    choice_text=choice_text,
                    is_correct=is_correct,
                    order=order
                )
                choice.full_clean()
                choice.save()
                return choice
        except ValidationError as e:
            raise

    @staticmethod
    def get_choice_by_id(choice_id: int) -> Optional[Choice]:
        try:
            return Choice.objects.get(id=choice_id)
        except Choice.DoesNotExist:
            return None

    @staticmethod
    def get_choices_by_question(question_id: int) -> List[Choice]:
        return Choice.objects.filter(question_id=question_id).order_by('order')

    @staticmethod
    def update_choice(choice: Choice, update_data: Dict[str, Any]) -> Choice:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(choice, field):
                        setattr(choice, field, value)
                choice.full_clean()
                choice.save()
                return choice
        except ValidationError as e:
            raise

    @staticmethod
    def delete_choice(choice: Choice) -> bool:
        try:
            choice.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def bulk_create_choices(question: Question, choices_data: List[Dict]) -> List[Choice]:
        choices = []
        with transaction.atomic():
            for idx, data in enumerate(choices_data):
                choice = Choice(
                    question=question,
                    choice_text=data['text'],
                    is_correct=data.get('is_correct', False),
                    order=data.get('order', idx)
                )
                choice.full_clean()
                choice.save()
                choices.append(choice)
        return choices