from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.final_grade import FinalGrade
from students.models.student import Student
from academic.models.subject import Subject
from enrollments.models.enrollment import Enrollment
from classes.models.academic_year import AcademicYear
from common.enums.grades import GradeStatus

class FinalGradeService:
    """Service for FinalGrade model operations"""

    @staticmethod
    def create_final_grade(
        student: Student,
        subject: Subject,
        enrollment: Enrollment,
        academic_year: AcademicYear,
        q1_grade: Optional[Decimal] = None,
        q2_grade: Optional[Decimal] = None,
        q3_grade: Optional[Decimal] = None,
        q4_grade: Optional[Decimal] = None,
        final_grade: Optional[Decimal] = None,
        remarks: str = "",
        status: str = GradeStatus.DRAFT
    ) -> FinalGrade:
        try:
            with transaction.atomic():
                existing = FinalGrade.objects.filter(
                    student=student,
                    subject=subject,
                    enrollment=enrollment
                ).first()
                if existing:
                    raise ValidationError("Final grade already exists for this student and subject")

                final = FinalGrade(
                    student=student,
                    subject=subject,
                    enrollment=enrollment,
                    academic_year=academic_year,
                    q1_grade=q1_grade,
                    q2_grade=q2_grade,
                    q3_grade=q3_grade,
                    q4_grade=q4_grade,
                    final_grade=final_grade,
                    remarks=remarks,
                    status=status
                )
                final.full_clean()
                final.save()
                return final
        except ValidationError as e:
            raise

    @staticmethod
    def get_final_grade_by_id(final_id: int) -> Optional[FinalGrade]:
        try:
            return FinalGrade.objects.get(id=final_id)
        except FinalGrade.DoesNotExist:
            return None

    @staticmethod
    def get_final_grades_by_student(student_id: int, academic_year_id: Optional[int] = None) -> List[FinalGrade]:
        queryset = FinalGrade.objects.filter(student_id=student_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.select_related('subject')

    @staticmethod
    def update_final_grade(final: FinalGrade, update_data: Dict[str, Any]) -> FinalGrade:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(final, field):
                        setattr(final, field, value)
                final.full_clean()
                final.save()
                return final
        except ValidationError as e:
            raise

    @staticmethod
    def compute_final_grade(final: FinalGrade) -> Decimal:
        """Compute final grade from quarters (average of Q1-Q4)"""
        grades = [final.q1_grade, final.q2_grade, final.q3_grade, final.q4_grade]
        valid_grades = [g for g in grades if g is not None]
        if not valid_grades:
            return Decimal('0')
        avg = sum(valid_grades) / len(valid_grades)
        final.final_grade = avg
        final.save()
        return avg

    @staticmethod
    def delete_final_grade(final: FinalGrade) -> bool:
        try:
            final.delete()
            return True
        except Exception:
            return False