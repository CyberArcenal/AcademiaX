from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.student_achievement import StudentAchievement
from ..models.student import Student

class StudentAchievementService:
    """Service for StudentAchievement model operations"""

    @staticmethod
    def create_achievement(
        student: Student,
        title: str,
        awarding_body: str,
        date_awarded: date,
        level: str,
        description: str = "",
        certificate_url: str = ""
    ) -> StudentAchievement:
        try:
            with transaction.atomic():
                achievement = StudentAchievement(
                    student=student,
                    title=title,
                    awarding_body=awarding_body,
                    date_awarded=date_awarded,
                    level=level,
                    description=description,
                    certificate_url=certificate_url
                )
                achievement.full_clean()
                achievement.save()
                return achievement
        except ValidationError as e:
            raise

    @staticmethod
    def get_achievement_by_id(achievement_id: int) -> Optional[StudentAchievement]:
        try:
            return StudentAchievement.objects.get(id=achievement_id)
        except StudentAchievement.DoesNotExist:
            return None

    @staticmethod
    def get_achievements_by_student(student_id: int) -> List[StudentAchievement]:
        return StudentAchievement.objects.filter(student_id=student_id).order_by('-date_awarded')

    @staticmethod
    def update_achievement(achievement: StudentAchievement, update_data: Dict[str, Any]) -> StudentAchievement:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(achievement, field):
                        setattr(achievement, field, value)
                achievement.full_clean()
                achievement.save()
                return achievement
        except ValidationError as e:
            raise

    @staticmethod
    def delete_achievement(achievement: StudentAchievement) -> bool:
        try:
            achievement.delete()
            return True
        except Exception:
            return False