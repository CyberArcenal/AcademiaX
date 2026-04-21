import logging
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class AnnouncementStateTransitionService:
    """Handles side effects of announcement state changes."""

    @staticmethod
    def handle_creation(announcement):
        """When a new announcement is created, log it."""
        logger.info(f"Announcement {announcement.id} created by {announcement.author}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'is_published' in changes:
            AnnouncementStateTransitionService._handle_publish_change(
                instance, changes['is_published']['old'], changes['is_published']['new']
            )

    @staticmethod
    def _handle_publish_change(announcement, old_value, new_value):
        """When announcement is published or unpublished."""
        from communication.services.broadcast_log import BroadcastLogService
        from communication.services.notification import NotificationService

        if new_value is True and old_value is False:
            # Published: trigger broadcast to target audience
            announcement.published_at = timezone.now()
            announcement.save(update_fields=['published_at'])

            # Determine recipients based on target_audience
            recipients = []
            if announcement.target_audience == 'ALL':
                recipients = User.objects.filter(is_active=True)
            elif announcement.target_audience == 'STUDENTS':
                recipients = User.objects.filter(role='STUDENT', is_active=True)
            elif announcement.target_audience == 'TEACHERS':
                recipients = User.objects.filter(role='TEACHER', is_active=True)
            elif announcement.target_audience == 'STAFF':
                recipients = User.objects.filter(role__in=['ADMIN', 'STAFF'], is_active=True)
            elif announcement.target_audience == 'PARENTS':
                recipients = User.objects.filter(role='PARENT', is_active=True)
            elif announcement.target_audience == 'GRADE_LEVEL' and announcement.grade_level:
                # Get students in that grade level via enrollments
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(
                    grade_level=announcement.grade_level,
                    status='ENR'
                ).values_list('student__user_id', flat=True)
                recipients = User.objects.filter(id__in=student_ids)
            elif announcement.target_audience == 'SECTION' and announcement.section:
                student_ids = announcement.section.enrollments.filter(status='ENR').values_list('student__user_id', flat=True)
                recipients = User.objects.filter(id__in=student_ids)

            # Create broadcast logs and send notifications
            for recipient in recipients:
                # Create log
                BroadcastLogService.create_log(
                    announcement=announcement,
                    recipient=recipient,
                    channel='APP',
                    status='PENDING'
                )
                # Create in-app notification
                NotificationService.create_notification(
                    recipient=recipient,
                    title=announcement.title,
                    message=announcement.content,
                    notification_type='INFO',
                    channel='IN_APP'
                )
                # Optionally send email/SMS based on channels
                if 'EMAIL' in announcement.channels:
                    # Placeholder for email sending (would integrate with email service)
                    pass
                if 'SMS' in announcement.channels:
                    # Placeholder for SMS sending
                    pass

            logger.info(f"Announcement {announcement.id} published, sent to {recipients.count()} recipients")
        elif new_value is False and old_value is True:
            # Unpublished: no side effects, just log
            logger.info(f"Announcement {announcement.id} unpublished")