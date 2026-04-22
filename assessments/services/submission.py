from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any

from assessments.models.submission import Submission
from assessments.models.assessment import Assessment
from students.models.student import Student
from common.enums.assessment import SubmissionStatus

class SubmissionService:
    """Service for Submission model operations"""

    @staticmethod
    def create_submission(
        assessment: Assessment,
        student: Student,
        ip_address: Optional[str] = None,
        status: str = SubmissionStatus.SUBMITTED
    ) -> Submission:
        try:
            with transaction.atomic():
                # Check if submission already exists
                existing = Submission.objects.filter(assessment=assessment, student=student).first()
                if existing:
                    raise ValidationError("Student already has a submission for this assessment")

                # Check attempts limit
                attempts_count = Submission.objects.filter(assessment=assessment, student=student).count()
                if attempts_count >= assessment.attempts_allowed:
                    raise ValidationError(f"Maximum attempts ({assessment.attempts_allowed}) reached")

                submission = Submission(
                    assessment=assessment,
                    student=student,
                    ip_address=ip_address,
                    status=status
                )
                submission.full_clean()
                submission.save()
                return submission
        except ValidationError as e:
            raise

    @staticmethod
    def get_submission_by_id(submission_id: int) -> Optional[Submission]:
        try:
            return Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return None

    @staticmethod
    def get_submission_by_assessment_student(assessment_id: int, student_id: int) -> Optional[Submission]:
        try:
            return Submission.objects.get(assessment_id=assessment_id, student_id=student_id)
        except Submission.DoesNotExist:
            return None

    @staticmethod
    def get_submissions_by_assessment(assessment_id: int) -> List[Submission]:
        return Submission.objects.filter(assessment_id=assessment_id).select_related('student')

    @staticmethod
    def get_submissions_by_student(student_id: int) -> List[Submission]:
        return Submission.objects.filter(student_id=student_id).select_related('assessment')

    @staticmethod
    def update_submission(submission: Submission, update_data: Dict[str, Any]) -> Submission:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(submission, field):
                        setattr(submission, field, value)
                submission.full_clean()
                submission.save()
                return submission
        except ValidationError as e:
            raise

    @staticmethod
    def grade_submission(
        submission: Submission,
        score: float,
        graded_by_id: int,
        feedback: str = ""
    ) -> Submission:
        submission.score = score
        submission.graded_by_id = graded_by_id
        submission.graded_at = timezone.now()
        submission.status = SubmissionStatus.GRADED
        submission.feedback = feedback
        submission.save()
        return submission

    @staticmethod
    def delete_submission(submission: Submission) -> bool:
        try:
            submission.delete()
            return True
        except Exception:
            return False