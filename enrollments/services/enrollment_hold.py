from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List
from decimal import Decimal

from ..models.enrollment_hold import EnrollmentHold
from ..models.enrollment import Enrollment
from ...users.models import User

class EnrollmentHoldService:
    """Service for EnrollmentHold model operations"""

    @staticmethod
    def create_hold(
        enrollment: Enrollment,
        reason: str,
        amount_due: Decimal = Decimal('0')
    ) -> EnrollmentHold:
        try:
            with transaction.atomic():
                # Check if hold already exists
                existing = EnrollmentHold.objects.filter(enrollment=enrollment, is_resolved=False).first()
                if existing:
                    raise ValidationError("Enrollment already has an unresolved hold")

                hold = EnrollmentHold(
                    enrollment=enrollment,
                    reason=reason,
                    amount_due=amount_due,
                    is_resolved=False
                )
                hold.full_clean()
                hold.save()
                return hold
        except ValidationError as e:
            raise

    @staticmethod
    def get_hold_by_id(hold_id: int) -> Optional[EnrollmentHold]:
        try:
            return EnrollmentHold.objects.get(id=hold_id)
        except EnrollmentHold.DoesNotExist:
            return None

    @staticmethod
    def get_hold_by_enrollment(enrollment_id: int) -> Optional[EnrollmentHold]:
        try:
            return EnrollmentHold.objects.get(enrollment_id=enrollment_id, is_resolved=False)
        except EnrollmentHold.DoesNotExist:
            return None

    @staticmethod
    def get_all_active_holds() -> List[EnrollmentHold]:
        return EnrollmentHold.objects.filter(is_resolved=False).select_related('enrollment')

    @staticmethod
    def resolve_hold(hold: EnrollmentHold, resolved_by: User) -> EnrollmentHold:
        hold.is_resolved = True
        hold.resolved_at = timezone.now()
        hold.resolved_by = resolved_by
        hold.save()
        return hold

    @staticmethod
    def update_hold(hold: EnrollmentHold, reason: str, amount_due: Decimal) -> EnrollmentHold:
        hold.reason = reason
        hold.amount_due = amount_due
        hold.save()
        return hold

    @staticmethod
    def delete_hold(hold: EnrollmentHold) -> bool:
        try:
            hold.delete()
            return True
        except Exception:
            return False