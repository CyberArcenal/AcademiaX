from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date


from academic.models.subject import Subject
from enrollments.models.enrollment import Enrollment
from enrollments.models.subject_enrollment import SubjectEnrollment
from teachers.models.teacher import Teacher
from common.enums.enrollment import DropReason

class SubjectEnrollmentService:
    """Service for SubjectEnrollment model operations"""

    @staticmethod
    def enroll_subject(
        enrollment: Enrollment,
        subject: Subject,
        teacher: Optional[Teacher] = None
    ) -> SubjectEnrollment:
        try:
            with transaction.atomic():
                # Check if already enrolled
                existing = SubjectEnrollment.objects.filter(enrollment=enrollment, subject=subject).first()
                if existing:
                    raise ValidationError(f"Student already enrolled in {subject.code}")

                subject_enrollment = SubjectEnrollment(
                    enrollment=enrollment,
                    subject=subject,
                    teacher=teacher,
                    is_dropped=False
                )
                subject_enrollment.full_clean()
                subject_enrollment.save()
                return subject_enrollment
        except ValidationError as e:
            raise

    @staticmethod
    def get_subject_enrollment_by_id(subj_enr_id: int) -> Optional[SubjectEnrollment]:
        try:
            return SubjectEnrollment.objects.get(id=subj_enr_id)
        except SubjectEnrollment.DoesNotExist:
            return None

    @staticmethod
    def get_subject_enrollments_by_enrollment(enrollment_id: int, include_dropped: bool = False) -> List[SubjectEnrollment]:
        queryset = SubjectEnrollment.objects.filter(enrollment_id=enrollment_id)
        if not include_dropped:
            queryset = queryset.filter(is_dropped=False)
        return queryset.select_related('subject', 'teacher')

    @staticmethod
    def drop_subject(
        subject_enrollment: SubjectEnrollment,
        reason: str,
        drop_date: Optional[date] = None
    ) -> SubjectEnrollment:
        subject_enrollment.is_dropped = True
        subject_enrollment.drop_date = drop_date or date.today()
        subject_enrollment.drop_reason = reason
        subject_enrollment.save()
        return subject_enrollment

    @staticmethod
    def update_final_grade(subject_enrollment: SubjectEnrollment, final_grade: Decimal) -> SubjectEnrollment:
        subject_enrollment.final_grade = final_grade
        subject_enrollment.save()
        return subject_enrollment

    @staticmethod
    def delete_subject_enrollment(subject_enrollment: SubjectEnrollment) -> bool:
        try:
            subject_enrollment.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def bulk_enroll_subjects(enrollment: Enrollment, subject_ids: List[int], teacher_ids: Dict[int, int] = None) -> List[SubjectEnrollment]:
        created = []
        with transaction.atomic():
            for subject_id in subject_ids:
                teacher_id = teacher_ids.get(subject_id) if teacher_ids else None
                teacher = Teacher.objects.get(id=teacher_id) if teacher_id else None
                subject = Subject.objects.get(id=subject_id)
                subj_enr = SubjectEnrollment.objects.create(
                    enrollment=enrollment,
                    subject=subject,
                    teacher=teacher,
                    is_dropped=False
                )
                created.append(subj_enr)
        return created