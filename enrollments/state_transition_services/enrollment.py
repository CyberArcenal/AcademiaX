import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class EnrollmentStateTransitionService:
    """Handles side effects of enrollment state changes."""

    @staticmethod
    def handle_creation(enrollment):
        """When a new enrollment is created, generate fee assessments and update section count."""
        # 1. Update section current enrollment count
        enrollment.section.current_enrollment += 1
        enrollment.section.save()
        logger.info(f"Incremented section {enrollment.section.id} enrollment count by 1")

        # 2. Generate fee assessments based on fee structure
        from fees.services.fee_structure import FeeStructureService
        from fees.services.fee_assessment import FeeAssessmentService

        fee_structures = FeeStructureService.get_fee_structures_for_student(
            grade_level_id=enrollment.grade_level_id,
            academic_program_id=None,  # optional, could be derived from curriculum
            academic_year_id=enrollment.academic_year_id
        )
        for fs in fee_structures:
            FeeAssessmentService.create_assessment(
                enrollment=enrollment,
                fee_structure=fs,
                amount=fs.amount,
                due_date=fs.due_date or enrollment.academic_year.end_date
            )
        logger.info(f"Generated {len(fee_structures)} fee assessments for enrollment {enrollment.id}")

        # 3. Optionally, create subject enrollments based on curriculum
        from academic.services.curriculum import CurriculumService
        from enrollments.services.subject_enrollment import SubjectEnrollmentService

        curriculum = CurriculumService.get_current_curriculum(
            enrollment.grade_level_id, enrollment.academic_year_id  # adjust parameters if needed
        )
        if curriculum:
            curriculum_subjects = curriculum.curriculum_subjects.filter(is_required=True)
            for cs in curriculum_subjects:
                SubjectEnrollmentService.enroll_subject(
                    enrollment=enrollment,
                    subject=cs.subject,
                    teacher=None  # can be assigned later
                )
            logger.info(f"Enrolled {curriculum_subjects.count()} required subjects for enrollment {enrollment.id}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            EnrollmentStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )
        if 'payment_status' in changes:
            EnrollmentStateTransitionService._handle_payment_status_change(
                instance, changes['payment_status']['old'], changes['payment_status']['new']
            )
        if 'section' in changes:
            EnrollmentStateTransitionService._handle_section_change(
                instance, changes['section']['old'], changes['section']['new']
            )

    @staticmethod
    def _handle_status_change(enrollment, old_status, new_status):
        """Handle enrollment status transitions."""
        # When enrollment becomes ENROLLED (approved)
        if new_status == 'ENR' and old_status != 'ENR':
            # Ensure section count is correct (already incremented at creation, but just in case)
            # Also maybe trigger welcome notification
            from communication.services.notification import NotificationService
            if enrollment.student.user:
                NotificationService.create_notification(
                    recipient=enrollment.student.user,
                    title="Enrollment Approved",
                    message=f"Your enrollment for {enrollment.academic_year.name} has been approved.",
                    notification_type='INFO'
                )
            logger.info(f"Enrollment {enrollment.id} approved, notification sent")

        # When enrollment is dropped
        if new_status == 'DRP' and old_status != 'DRP':
            # Decrement section count
            enrollment.section.current_enrollment -= 1
            enrollment.section.save()
            # Also drop all subject enrollments
            from enrollments.services.subject_enrollment import SubjectEnrollmentService
            subject_enrollments = enrollment.subject_enrollments.filter(is_dropped=False)
            for se in subject_enrollments:
                SubjectEnrollmentService.drop_subject(se, reason=enrollment.drop_reason or "Enrollment dropped")
            logger.info(f"Dropped enrollment {enrollment.id}, removed {subject_enrollments.count()} subject enrollments")

        # When enrollment is transferred
        if new_status == 'TRF' and old_status != 'TRF':
            enrollment.section.current_enrollment -= 1
            enrollment.section.save()
            logger.info(f"Enrollment {enrollment.id} transferred out, section count decreased")

        # When enrollment is on leave
        if new_status == 'LV' and old_status != 'LV':
            # Optionally freeze subject enrollments
            logger.info(f"Enrollment {enrollment.id} put on leave")

    @staticmethod
    def _handle_payment_status_change(enrollment, old_status, new_status):
        """When payment status changes, update enrollment status if fully paid."""
        if new_status == 'PD' and old_status != 'PD':
            # If payment is complete and enrollment is pending, auto-approve?
            if enrollment.status == 'PND':
                enrollment.status = 'ENR'
                enrollment.save()
                logger.info(f"Enrollment {enrollment.id} auto-approved due to full payment")

    @staticmethod
    def _handle_section_change(enrollment, old_section_id, new_section_id):
        """When section is changed, update counts on both sections."""
        if old_section_id:
            from classes.services.section import SectionService
            old_section = SectionService.get_section_by_id(old_section_id)
            if old_section:
                old_section.current_enrollment -= 1
                old_section.save()
                logger.info(f"Decremented old section {old_section_id} enrollment")
        if new_section_id:
            new_section = SectionService.get_section_by_id(new_section_id)
            if new_section:
                new_section.current_enrollment += 1
                new_section.save()
                logger.info(f"Incremented new section {new_section_id} enrollment")