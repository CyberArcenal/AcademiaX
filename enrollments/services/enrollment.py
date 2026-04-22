from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import date
from enrollments.models.enrollment import Enrollment
from students.models.student import Student
from classes.models.academic_year import AcademicYear
from classes.models.grade_level import GradeLevel
from classes.models.section import Section
from users.models import User
from common.enums.enrollment import EnrollmentStatus, DropReason, EnrollmentPaymentStatus

class EnrollmentService:
    """Service for Enrollment model operations"""

    @staticmethod
    def create_enrollment(
        student: Student,
        academic_year: AcademicYear,
        grade_level: GradeLevel,
        section: Section,
        processed_by: Optional[User] = None,
        enrollment_date: Optional[date] = None,
        previous_school: str = "",
        lrn: str = "",
        status: str = EnrollmentStatus.PENDING,
        payment_status: str = EnrollmentPaymentStatus.UNPAID,
        remarks: str = ""
    ) -> Enrollment:
        try:
            with transaction.atomic():
                # Check if student already has enrollment for this academic year
                existing = Enrollment.objects.filter(student=student, academic_year=academic_year).first()
                if existing:
                    raise ValidationError(f"Student already has an enrollment for {academic_year.name}")

                # Check section capacity
                if section.current_enrollment >= section.capacity:
                    raise ValidationError(f"Section {section.name} is already full")

                enrollment = Enrollment(
                    student=student,
                    academic_year=academic_year,
                    grade_level=grade_level,
                    section=section,
                    enrollment_date=enrollment_date or date.today(),
                    status=status,
                    payment_status=payment_status,
                    previous_school=previous_school,
                    lrn=lrn,
                    remarks=remarks,
                    processed_by=processed_by
                )
                enrollment.full_clean()
                enrollment.save()

                # Update section current enrollment
                section.current_enrollment += 1
                section.save()

                # Create enrollment history entry
                from .enrollment_history import EnrollmentHistoryService
                EnrollmentHistoryService.create_history(
                    enrollment=enrollment,
                    previous_status=None,
                    new_status=status,
                    remarks="Initial enrollment created"
                )

                return enrollment
        except ValidationError as e:
            raise

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int) -> Optional[Enrollment]:
        try:
            return Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return None

    @staticmethod
    def get_enrollment_by_student_year(student_id: int, academic_year_id: int) -> Optional[Enrollment]:
        try:
            return Enrollment.objects.get(student_id=student_id, academic_year_id=academic_year_id)
        except Enrollment.DoesNotExist:
            return None

    @staticmethod
    def get_enrollments_by_student(student_id: int) -> List[Enrollment]:
        return Enrollment.objects.filter(student_id=student_id).order_by('-academic_year__start_date')

    @staticmethod
    def get_enrollments_by_section(section_id: int, academic_year_id: Optional[int] = None) -> List[Enrollment]:
        queryset = Enrollment.objects.filter(section_id=section_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.select_related('student')

    @staticmethod
    def get_enrollments_by_status(status: str, academic_year_id: Optional[int] = None) -> List[Enrollment]:
        queryset = Enrollment.objects.filter(status=status)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset

    @staticmethod
    def update_enrollment(enrollment: Enrollment, update_data: Dict[str, Any]) -> Enrollment:
        try:
            with transaction.atomic():
                # Track status change for history
                old_status = enrollment.status

                for field, value in update_data.items():
                    if hasattr(enrollment, field):
                        setattr(enrollment, field, value)

                enrollment.full_clean()
                enrollment.save()

                # Create history if status changed
                if 'status' in update_data and update_data['status'] != old_status:
                    from .enrollment_history import EnrollmentHistoryService
                    EnrollmentHistoryService.create_history(
                        enrollment=enrollment,
                        previous_status=old_status,
                        new_status=enrollment.status,
                        remarks=update_data.get('remarks', 'Status updated')
                    )

                # If section changed, update section counts
                if 'section' in update_data and update_data['section'] != enrollment.section:
                    # Decrement old section count (if old section exists)
                    old_section = update_data.get('_old_section')  # This would need to be handled differently
                    # Better: handle section change via separate method
                    pass

                return enrollment
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(
        enrollment: Enrollment,
        status: str,
        drop_reason: Optional[str] = None,
        drop_date: Optional[date] = None,
        remarks: str = ""
    ) -> Enrollment:
        try:
            with transaction.atomic():
                old_status = enrollment.status
                enrollment.status = status
                if status == EnrollmentStatus.DROPPED:
                    enrollment.drop_reason = drop_reason
                    enrollment.drop_date = drop_date or date.today()
                    # Decrement section enrollment count
                    enrollment.section.current_enrollment -= 1
                    enrollment.section.save()
                enrollment.remarks = remarks or enrollment.remarks
                enrollment.save()

                # Create history
                from .enrollment_history import EnrollmentHistoryService
                EnrollmentHistoryService.create_history(
                    enrollment=enrollment,
                    previous_status=old_status,
                    new_status=status,
                    reason=drop_reason,
                    remarks=remarks
                )
                return enrollment
        except ValidationError as e:
            raise

    @staticmethod
    def delete_enrollment(enrollment: Enrollment, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                enrollment.is_active = False
                enrollment.save()
                # Restore section count
                enrollment.section.current_enrollment -= 1
                enrollment.section.save()
            else:
                # Hard delete: restore section count before deletion
                enrollment.section.current_enrollment -= 1
                enrollment.section.save()
                enrollment.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_enrollments(query: str, academic_year_id: Optional[int] = None, limit: int = 20) -> List[Enrollment]:
        from django.db import models
        queryset = Enrollment.objects.filter(
            models.Q(student__first_name__icontains=query) |
            models.Q(student__last_name__icontains=query) |
            models.Q(student__student_id__icontains=query) |
            models.Q(lrn__icontains=query)
        )
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset[:limit]

    @staticmethod
    def transfer_section(enrollment: Enrollment, new_section: Section) -> Enrollment:
        """Transfer student to a different section within same grade level"""
        try:
            with transaction.atomic():
                if new_section.current_enrollment >= new_section.capacity:
                    raise ValidationError(f"New section {new_section.name} is full")

                # Remove from old section
                enrollment.section.current_enrollment -= 1
                enrollment.section.save()

                # Add to new section
                enrollment.section = new_section
                enrollment.save()
                new_section.current_enrollment += 1
                new_section.save()

                # Create history
                from .enrollment_history import EnrollmentHistoryService
                EnrollmentHistoryService.create_history(
                    enrollment=enrollment,
                    previous_status=enrollment.status,
                    new_status=enrollment.status,
                    remarks=f"Transferred from section {enrollment.section.name} to {new_section.name}"
                )
                return enrollment
        except ValidationError as e:
            raise