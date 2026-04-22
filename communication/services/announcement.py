from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any

from communication.models.announcement import Announcement
from users.models import User
from classes.models.grade_level import GradeLevel
from classes.models.section import Section
from common.enums.communication import TargetAudience, NotificationChannel

class AnnouncementService:
    """Service for Announcement model operations"""

    @staticmethod
    def create_announcement(
        title: str,
        content: str,
        author: User,
        target_audience: str = TargetAudience.ALL,
        grade_level: Optional[GradeLevel] = None,
        section: Optional[Section] = None,
        channels: List[str] = None,
        scheduled_at: Optional[timezone.datetime] = None,
        expires_at: Optional[timezone.datetime] = None,
        attachment_urls: List[str] = None
    ) -> Announcement:
        try:
            with transaction.atomic():
                announcement = Announcement(
                    title=title,
                    content=content,
                    author=author,
                    target_audience=target_audience,
                    grade_level=grade_level,
                    section=section,
                    channels=channels or [NotificationChannel.IN_APP],
                    scheduled_at=scheduled_at,
                    expires_at=expires_at,
                    attachment_urls=attachment_urls or [],
                    is_published=False
                )
                announcement.full_clean()
                announcement.save()
                return announcement
        except ValidationError as e:
            raise

    @staticmethod
    def get_announcement_by_id(announcement_id: int) -> Optional[Announcement]:
        try:
            return Announcement.objects.get(id=announcement_id)
        except Announcement.DoesNotExist:
            return None

    @staticmethod
    def get_published_announcements(limit: int = 20) -> List[Announcement]:
        now = timezone.now()
        return Announcement.objects.filter(
            is_published=True,
            published_at__lte=now,
            expires_at__gt=now
        ).order_by('-published_at')[:limit]

    @staticmethod
    def get_announcements_by_author(author_id: int) -> List[Announcement]:
        return Announcement.objects.filter(author_id=author_id).order_by('-created_at')

    @staticmethod
    def update_announcement(announcement: Announcement, update_data: Dict[str, Any]) -> Announcement:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(announcement, field):
                        setattr(announcement, field, value)
                announcement.full_clean()
                announcement.save()
                return announcement
        except ValidationError as e:
            raise

    @staticmethod
    def publish_announcement(announcement: Announcement) -> Announcement:
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.save()
        return announcement

    @staticmethod
    def delete_announcement(announcement: Announcement, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                announcement.is_active = False
                announcement.save()
            else:
                announcement.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_announcements_for_user(user: User) -> List[Announcement]:
        """Get announcements relevant to a user based on their role and associations"""
        now = timezone.now()
        queryset = Announcement.objects.filter(
            is_published=True,
            published_at__lte=now,
            expires_at__gt=now
        )
        # Filter by target audience (simplified: check if user has student/teacher/parent profile)
        # This would require more complex logic based on actual user roles
        return queryset.order_by('-published_at')