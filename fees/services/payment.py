from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date

from ..models.payment import Payment
from ..models.fee_assessment import FeeAssessment
from ...users.models import User

class PaymentService:
    """Service for Payment model operations"""

    @staticmethod
    def generate_reference_number() -> str:
        import random
        import string
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"PAY-{timestamp}-{random_str}"

    @staticmethod
    def process_payment(
        assessment: FeeAssessment,
        amount: Decimal,
        payment_date: date,
        payment_method: str,
        received_by: Optional[User] = None,
        reference_number: str = "",
        check_number: str = "",
        bank_name: str = "",
        notes: str = "",
        is_verified: bool = True
    ) -> Payment:
        try:
            with transaction.atomic():
                if amount <= 0:
                    raise ValidationError("Payment amount must be positive")
                if amount > assessment.balance:
                    raise ValidationError(f"Payment amount exceeds outstanding balance of {assessment.balance}")

                payment = Payment(
                    assessment=assessment,
                    amount=amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    reference_number=reference_number or PaymentService.generate_reference_number(),
                    check_number=check_number,
                    bank_name=bank_name,
                    received_by=received_by,
                    notes=notes,
                    is_verified=is_verified
                )
                payment.full_clean()
                payment.save()

                # Update assessment balance
                from .fee_assessment import FeeAssessmentService
                FeeAssessmentService.update_balance(assessment, amount)

                return payment
        except ValidationError as e:
            raise

    @staticmethod
    def get_payment_by_id(payment_id: int) -> Optional[Payment]:
        try:
            return Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return None

    @staticmethod
    def get_payments_by_assessment(assessment_id: int) -> List[Payment]:
        return Payment.objects.filter(assessment_id=assessment_id).order_by('-payment_date')

    @staticmethod
    def get_payments_by_date_range(start_date: date, end_date: date) -> List[Payment]:
        return Payment.objects.filter(payment_date__gte=start_date, payment_date__lte=end_date)

    @staticmethod
    def update_payment(payment: Payment, update_data: Dict[str, Any]) -> Payment:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(payment, field):
                        setattr(payment, field, value)
                payment.full_clean()
                payment.save()
                return payment
        except ValidationError as e:
            raise

    @staticmethod
    def verify_payment(payment: Payment) -> Payment:
        payment.is_verified = True
        payment.save()
        return payment

    @staticmethod
    def delete_payment(payment: Payment) -> bool:
        try:
            # Restore assessment balance before deleting
            payment.assessment.balance += payment.amount
            if payment.assessment.balance == payment.assessment.amount:
                payment.assessment.status = 'PND'  # Pending
            elif payment.assessment.balance > 0:
                payment.assessment.status = 'PRT'  # Partial
            payment.assessment.save()
            payment.delete()
            return True
        except Exception:
            return False