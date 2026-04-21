from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List

from ..models.enrollment_history import EnrollmentHistory
from ..models.enrollment import Enrollment
from ...users.models import User
from ...common.enums.enrollment import EnrollmentStatus, DropReason

class EnrollmentHistoryService:
    """Service for EnrollmentHistory model operations"""

    @staticmethod
    def create_history(
        enrollment: Enrollment,
        previous_status: Optional[str],
        new_status: str,
        reason: Optional[str] = None,
        remarks: str = "",
        changed_by: Optional[User] = None
    ) -> EnrollmentHistory:
        try:
            with transaction.atomic():
                history = EnrollmentHistory(
                    enrollment=enrollment,
                    previous_status=previous_status,
                    new_status=new_status,
                    reason=reason,
                    remarks=remarks,
                    changed_by=changed_by
                )
                history.full_clean()
                history.save()
                return history
        except ValidationError as e:
            raise

    @staticmethod
    def get_history_by_enrollment(enrollment_id: int, limit: int = 50) -> List[EnrollmentHistory]:
        return EnrollmentHistory.objects.filter(enrollment_id=enrollment_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_history_by_id(history_id: int) -> Optional[EnrollmentHistory]:
        try:
            return EnrollmentHistory.objects.get(id=history_id)
        except EnrollmentHistory.DoesNotExist:
            return None

    @staticmethod
    def delete_history(history: EnrollmentHistory) -> bool:
        try:
            history.delete()
            return True
        except Exception:
            return False