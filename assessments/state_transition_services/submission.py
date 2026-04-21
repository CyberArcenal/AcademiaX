import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class SubmissionStateTransitionService:
    """Handles side effects of submission state changes."""

    @staticmethod
    def handle_creation(submission):
        """When a new submission is created, log it and notify teacher? Optional."""
        logger.info(f"Submission {submission.id} created by student {submission.student.id} for assessment {submission.assessment.id}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            SubmissionStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(submission, old_status, new_status):
        """When submission status changes."""
        from communication.services.notification import NotificationService

        # When submitted (status becomes SUBMITTED)
        if new_status == 'SB' and old_status != 'SB':
            # Notify teacher
            teacher = submission.assessment.teacher
            if teacher.user:
                NotificationService.create_notification(
                    recipient=teacher.user,
                    title="New Submission",
                    message=f"Student {submission.student.get_full_name()} submitted {submission.assessment.title}",
                    notification_type='INFO',
                    action_url=f"/assessments/{submission.assessment.id}/submissions/"
                )
            logger.info(f"Submission {submission.id} submitted, teacher notified")

        # When graded (status becomes GRADED)
        if new_status == 'GD' and old_status != 'GD':
            # Notify student
            if submission.student.user:
                NotificationService.create_notification(
                    recipient=submission.student.user,
                    title="Submission Graded",
                    message=f"Your submission for {submission.assessment.title} has been graded. Score: {submission.score}",
                    notification_type='GRADE_RELEASED'
                )
            logger.info(f"Submission {submission.id} graded, student notified")