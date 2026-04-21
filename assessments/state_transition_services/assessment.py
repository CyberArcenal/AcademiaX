import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class AssessmentStateTransitionService:
    """Handles side effects of assessment state changes."""

    @staticmethod
    def handle_creation(assessment):
        """When a new assessment is created, log it."""
        logger.info(f"Assessment {assessment.id} created for subject {assessment.subject.code}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'is_published' in changes:
            AssessmentStateTransitionService._handle_publish_change(
                instance, changes['is_published']['old'], changes['is_published']['new']
            )

    @staticmethod
    def _handle_publish_change(assessment, old_value, new_value):
        """When assessment is published or unpublished."""
        from communication.services.notification import NotificationService
        from enrollments.models import Enrollment
        from classes.models import Section

        if new_value is True and old_value is False:
            # Published: notify all enrolled students in the section(s) where this subject is taught
            # Get all sections for this subject and academic year (simplified: get sections via teaching assignments)
            from teachers.models import TeachingAssignment
            assignments = TeachingAssignment.objects.filter(
                subject=assessment.subject,
                academic_year=assessment.term.academic_year,
                is_active=True
            )
            section_ids = assignments.values_list('section_id', flat=True)
            enrollments = Enrollment.objects.filter(
                section_id__in=section_ids,
                status='ENR',
                academic_year=assessment.term.academic_year
            ).select_related('student')
            unique_students = set(e.student for e in enrollments)
            for student in unique_students:
                if student.user:
                    NotificationService.create_notification(
                        recipient=student.user,
                        title="New Assessment Published",
                        message=f"A new {assessment.get_assessment_type_display()} '{assessment.title}' has been published. Due: {assessment.due_date}",
                        notification_type='REMINDER'
                    )
            logger.info(f"Assessment {assessment.id} published, notified {len(unique_students)} students")
        elif new_value is False and old_value is True:
            # Unpublished: maybe notify that assessment is no longer available
            logger.info(f"Assessment {assessment.id} unpublished")