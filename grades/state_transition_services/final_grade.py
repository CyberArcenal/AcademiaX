import logging

logger = logging.getLogger(__name__)


class FinalGradeStateTransitionService:
    """Handles side effects of final grade changes."""

    @staticmethod
    def handle_creation(final_grade):
        """When a final grade is created, maybe generate report card update."""
        logger.info(f"Final grade {final_grade.id} created for student {final_grade.student.id}")

    @staticmethod
    def handle_update(final_grade):
        """When final grade is updated, update report card and transcript."""
        from grades.services.report_card import ReportCardService
        from grades.services.transcript import TranscriptService

        # Update or create report card for the term
        enrollment = final_grade.enrollment
        term = enrollment.term  # This may not be directly available; adjust as needed
        report_card = ReportCardService.get_report_card_by_student_term(
            final_grade.student.id,
            final_grade.academic_year.id,
            term.id
        )
        if report_card:
            # Recalculate GPA
            gpa = ReportCardService.compute_gpa_from_grades(
                final_grade.student.id,
                final_grade.academic_year.id,
                term.id
            )
            report_card.gpa = gpa
            report_card.save()
            logger.info(f"Report card {report_card.id} GPA updated to {gpa}")

        # Update cumulative GWA in transcript
        transcript = TranscriptService.get_transcript_by_student(final_grade.student.id)
        if transcript:
            gwa = TranscriptService.compute_cumulative_gwa(final_grade.student.id)
            transcript.cumulative_gwa = gwa
            transcript.save()
            logger.info(f"Transcript for student {final_grade.student.id} GWA updated to {gwa}")