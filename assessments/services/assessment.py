from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from assessments.models.assessment import Assessment
from academic.models.subject import Subject
from teachers.models.teacher import Teacher
from common.enums.assessment import AssessmentType

class AssessmentService:
    """Service for Assessment model operations"""

    @staticmethod
    def create_assessment(
        subject: Subject,
        teacher: Teacher,
        title: str,
        assessment_type: str,
        total_points: Decimal = 0,
        due_date: Optional[timezone.datetime] = None,
        open_date: Optional[timezone.datetime] = None,
        close_date: Optional[timezone.datetime] = None,
        duration_minutes: Optional[int] = None,
        passing_points: Optional[Decimal] = None,
        is_published: bool = False,
        allow_late_submission: bool = False,
        late_deduction_per_day: Decimal = Decimal('0'),
        attempts_allowed: int = 1,
        show_answers_after_submission: bool = False,
        description: str = ""
    ) -> Assessment:
        try:
            with transaction.atomic():
                assessment = Assessment(
                    subject=subject,
                    teacher=teacher,
                    title=title,
                    description=description,
                    assessment_type=assessment_type,
                    total_points=total_points,
                    passing_points=passing_points,
                    duration_minutes=duration_minutes,
                    due_date=due_date,
                    open_date=open_date,
                    close_date=close_date,
                    is_published=is_published,
                    allow_late_submission=allow_late_submission,
                    late_deduction_per_day=late_deduction_per_day,
                    attempts_allowed=attempts_allowed,
                    show_answers_after_submission=show_answers_after_submission
                )
                assessment.full_clean()
                assessment.save()
                return assessment
        except ValidationError as e:
            raise

    @staticmethod
    def get_assessment_by_id(assessment_id: int) -> Optional[Assessment]:
        try:
            return Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return None

    @staticmethod
    def get_assessments_by_subject(subject_id: int, published_only: bool = True) -> List[Assessment]:
        queryset = Assessment.objects.filter(subject_id=subject_id)
        if published_only:
            queryset = queryset.filter(is_published=True)
        return queryset.order_by('-created_at')

    @staticmethod
    def get_assessments_by_teacher(teacher_id: int) -> List[Assessment]:
        return Assessment.objects.filter(teacher_id=teacher_id).order_by('-created_at')

    @staticmethod
    def get_upcoming_assessments(teacher_id: Optional[int] = None, limit: int = 10) -> List[Assessment]:
        queryset = Assessment.objects.filter(
            due_date__gte=timezone.now(),
            is_published=True
        )
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        return queryset.order_by('due_date')[:limit]

    @staticmethod
    def update_assessment(assessment: Assessment, update_data: Dict[str, Any]) -> Assessment:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(assessment, field):
                        setattr(assessment, field, value)
                assessment.full_clean()
                assessment.save()
                return assessment
        except ValidationError as e:
            raise

    @staticmethod
    def publish_assessment(assessment: Assessment) -> Assessment:
        assessment.is_published = True
        assessment.save()
        return assessment

    @staticmethod
    def unpublish_assessment(assessment: Assessment) -> Assessment:
        assessment.is_published = False
        assessment.save()
        return assessment

    @staticmethod
    def delete_assessment(assessment: Assessment, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                assessment.is_active = False
                assessment.save()
            else:
                assessment.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def recalculate_total_points(assessment: Assessment) -> Decimal:
        total = sum(question.points for question in assessment.questions.all())
        assessment.total_points = total
        assessment.save()
        return total