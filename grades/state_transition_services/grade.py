import logging
from django.db import transaction

from grades.models.final_grade import FinalGrade

logger = logging.getLogger(__name__)


class GradeStateTransitionService:
    """Handles side effects of grade state changes."""

    @staticmethod
    def handle_creation(grade):
        """When a new grade is created, nothing special yet."""
        logger.info(f"Grade {grade.id} created for student {grade.student.id} in subject {grade.subject.code}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            GradeStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(grade, old_status, new_status):
        """When grade status changes."""
        # When grade is approved, update final grade if all quarterly grades are present
        if new_status == 'APP' and old_status != 'APP':
            # Check if this is a quarterly grade and if all quarters are present for this subject
            # This logic would be better placed in a final grade service, but for demonstration:
            from grades.services.final_grade import FinalGradeService
            enrollment = grade.enrollment
            subject = grade.subject
            term = grade.term
            # Get all grades for this enrollment, subject, and year
            grades_qs = enrollment.grades.filter(subject=subject, term__academic_year=term.academic_year)
            if grades_qs.count() == 4:  # Assuming 4 quarters
                # Compute average
                percentages = [g.percentage for g in grades_qs if g.percentage is not None]
                if percentages:
                    avg = sum(percentages) / len(percentages)
                    final_grade, _ = FinalGrade.objects.get_or_create(
                        student=enrollment.student,
                        subject=subject,
                        enrollment=enrollment,
                        academic_year=term.academic_year
                    )
                    final_grade.q1_grade = grades_qs.filter(term__term_number=1).first().percentage
                    final_grade.q2_grade = grades_qs.filter(term__term_number=2).first().percentage
                    final_grade.q3_grade = grades_qs.filter(term__term_number=3).first().percentage
                    final_grade.q4_grade = grades_qs.filter(term__term_number=4).first().percentage
                    final_grade.final_grade = avg
                    final_grade.save()
                    logger.info(f"Final grade computed for {enrollment.student.id} in {subject.code}: {avg}")
            logger.info(f"Grade {grade.id} approved")

        # When grade is posted, maybe notify student
        if new_status == 'PST' and old_status != 'PST':
            from communication.services.notification import NotificationService
            if grade.student.user:
                NotificationService.create_notification(
                    recipient=grade.student.user,
                    title="Grade Posted",
                    message=f"Your grade for {grade.subject.code} has been posted: {grade.percentage}%",
                    notification_type='GRADE_RELEASED'
                )
            logger.info(f"Grade {grade.id} posted, notification sent")