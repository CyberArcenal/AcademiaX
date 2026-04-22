from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date


from enrollments.models.enrollment import Enrollment
from classes.models.term import Term
from common.enums.fees import PaymentStatus
from fees.models.fee_assessment import FeeAssessment
from fees.models.fee_structure import FeeStructure

class FeeAssessmentService:
    """Service for FeeAssessment model operations"""

    @staticmethod
    def create_assessment(
        enrollment: Enrollment,
        fee_structure: FeeStructure,
        amount: Decimal,
        due_date: date,
        term: Optional[Term] = None,
        remarks: str = ""
    ) -> FeeAssessment:
        try:
            with transaction.atomic():
                assessment = FeeAssessment(
                    enrollment=enrollment,
                    fee_structure=fee_structure,
                    amount=amount,
                    due_date=due_date,
                    term=term,
                    status=PaymentStatus.PENDING,
                    balance=amount,
                    remarks=remarks
                )
                assessment.full_clean()
                assessment.save()
                return assessment
        except ValidationError as e:
            raise

    @staticmethod
    def get_assessment_by_id(assessment_id: int) -> Optional[FeeAssessment]:
        try:
            return FeeAssessment.objects.get(id=assessment_id)
        except FeeAssessment.DoesNotExist:
            return None

    @staticmethod
    def get_assessments_by_enrollment(enrollment_id: int) -> List[FeeAssessment]:
        return FeeAssessment.objects.filter(enrollment_id=enrollment_id).order_by('due_date')

    @staticmethod
    def get_outstanding_assessments(enrollment_id: int) -> List[FeeAssessment]:
        return FeeAssessment.objects.filter(
            enrollment_id=enrollment_id,
            status__in=[PaymentStatus.PENDING, PaymentStatus.PARTIAL, PaymentStatus.OVERDUE]
        ).order_by('due_date')

    @staticmethod
    def update_assessment(assessment: FeeAssessment, update_data: Dict[str, Any]) -> FeeAssessment:
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
    def update_balance(assessment: FeeAssessment, paid_amount: Decimal) -> FeeAssessment:
        new_balance = assessment.balance - paid_amount
        if new_balance <= 0:
            assessment.status = PaymentStatus.PAID
            assessment.balance = Decimal('0')
        else:
            assessment.status = PaymentStatus.PARTIAL
            assessment.balance = new_balance
        assessment.save()
        return assessment

    @staticmethod
    def mark_overdue() -> int:
        """Mark assessments as overdue if due date has passed and not paid"""
        today = date.today()
        count = FeeAssessment.objects.filter(
            due_date__lt=today,
            status__in=[PaymentStatus.PENDING, PaymentStatus.PARTIAL]
        ).update(status=PaymentStatus.OVERDUE)
        return count

    @staticmethod
    def delete_assessment(assessment: FeeAssessment) -> bool:
        try:
            assessment.delete()
            return True
        except Exception:
            return False