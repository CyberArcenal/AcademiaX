from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.achievement import AlumniAchievement
from ..models.alumni import Alumni

class AlumniAchievementService:
    """Service for AlumniAchievement model operations"""

    @staticmethod
    def create_achievement(
        alumni: Alumni,
        title: str,
        awarding_body: str,
        date_received: date,
        description: str = "",
        certificate_url: str = ""
    ) -> AlumniAchievement:
        try:
            with transaction.atomic():
                achievement = AlumniAchievement(
                    alumni=alumni,
                    title=title.title(),
                    awarding_body=awarding_body.title(),
                    date_received=date_received,
                    description=description,
                    certificate_url=certificate_url
                )
                achievement.full_clean()
                achievement.save()
                return achievement
        except ValidationError as e:
            raise

    @staticmethod
    def get_achievement_by_id(achievement_id: int) -> Optional[AlumniAchievement]:
        try:
            return AlumniAchievement.objects.get(id=achievement_id)
        except AlumniAchievement.DoesNotExist:
            return None

    @staticmethod
    def get_achievements_by_alumni(alumni_id: int) -> List[AlumniAchievement]:
        return AlumniAchievement.objects.filter(alumni_id=alumni_id).order_by('-date_received')

    @staticmethod
    def update_achievement(achievement: AlumniAchievement, update_data: Dict[str, Any]) -> AlumniAchievement:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(achievement, field):
                        if field in ['title', 'awarding_body']:
                            value = value.title()
                        setattr(achievement, field, value)
                achievement.full_clean()
                achievement.save()
                return achievement
        except ValidationError as e:
            raise

    @staticmethod
    def delete_achievement(achievement: AlumniAchievement) -> bool:
        try:
            achievement.delete()
            return True
        except Exception:
            return False