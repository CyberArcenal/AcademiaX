from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from grades.models.grade import Grade
from students.models.student import Student
from academic.models.subject import Subject
from enrollments.models.enrollment import Enrollment
from teachers.models.teacher import Teacher
from classes.models.term import Term
from users.models import User
from common.enums.grades import GradeStatus

class GradeService:
    """Service for Grade model operations"""

    @staticmethod
    def create_grade(
        student: Student,
        subject: Subject,
        enrollment: Enrollment,
        teacher: Teacher,
        term: Term,
        raw_score: Optional[Decimal] = None,
        percentage: Optional[Decimal] = None,
        transmuted_grade: Optional[Decimal] = None,
        letter_grade: str = "",
        remarks: str = "",
        graded_by: Optional[User] = None,
        status: str = GradeStatus.DRAFT
    ) -> Grade:
        try:
            with transaction.atomic():
                # Check if grade already exists for this combination
                existing = Grade.objects.filter(
                    student=student,
                    subject=subject,
                    enrollment=enrollment,
                    term=term
                ).first()
                if existing:
                    raise ValidationError("Grade already exists for this student, subject, enrollment, and term")

                grade = Grade(
                    student=student,
                    subject=subject,
                    enrollment=enrollment,
                    teacher=teacher,
                    term=term,
                    raw_score=raw_score,
                    percentage=percentage,
                    transmuted_grade=transmuted_grade,
                    letter_grade=letter_grade,
                    remarks=remarks,
                    graded_by=graded_by,
                    status=status
                )
                grade.full_clean()
                grade.save()
                return grade
        except ValidationError as e:
            raise

    @staticmethod
    def get_grade_by_id(grade_id: int) -> Optional[Grade]:
        try:
            return Grade.objects.get(id=grade_id)
        except Grade.DoesNotExist:
            return None

    @staticmethod
    def get_grades_by_student(student_id: int, term_id: Optional[int] = None) -> List[Grade]:
        queryset = Grade.objects.filter(student_id=student_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        return queryset.select_related('subject', 'teacher')

    @staticmethod
    def get_grades_by_enrollment(enrollment_id: int) -> List[Grade]:
        return Grade.objects.filter(enrollment_id=enrollment_id).select_related('subject')

    @staticmethod
    def get_grades_by_subject(subject_id: int, term_id: Optional[int] = None) -> List[Grade]:
        queryset = Grade.objects.filter(subject_id=subject_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        return queryset

    @staticmethod
    def update_grade(grade: Grade, update_data: Dict[str, Any]) -> Grade:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(grade, field):
                        setattr(grade, field, value)
                grade.full_clean()
                grade.save()
                return grade
        except ValidationError as e:
            raise

    @staticmethod
    def submit_grade(grade: Grade) -> Grade:
        grade.status = GradeStatus.SUBMITTED
        grade.graded_at = timezone.now()
        grade.save()
        return grade

    @staticmethod
    def approve_grade(grade: Grade) -> Grade:
        grade.status = GradeStatus.APPROVED
        grade.save()
        return grade

    @staticmethod
    def delete_grade(grade: Grade, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                grade.is_active = False
                grade.save()
            else:
                grade.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def calculate_percentage(raw_score: Decimal, total_points: Decimal) -> Decimal:
        if total_points == 0:
            return Decimal('0')
        return (raw_score / total_points) * 100

    @staticmethod
    def get_average_grade(student_id: int, term_id: int) -> Decimal:
        grades = Grade.objects.filter(student_id=student_id, term_id=term_id, status=GradeStatus.APPROVED)
        if not grades:
            return Decimal('0')
        total = sum((g.percentage or 0) for g in grades)
        return total / len(grades)