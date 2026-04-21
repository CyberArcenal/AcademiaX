from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.teacher_qualification import TeacherQualification
from ..models.teacher import Teacher

class TeacherQualificationService:
    """Service for TeacherQualification model operations"""

    @staticmethod
    def create_qualification(
        teacher: Teacher,
        qualification_name: str,
        issuing_body: str,
        date_earned: date,
        expiry_date: Optional[date] = None,
        attachment_url: str = ""
    ) -> TeacherQualification:
        try:
            with transaction.atomic():
                qualification = TeacherQualification(
                    teacher=teacher,
                    qualification_name=qualification_name,
                    issuing_body=issuing_body,
                    date_earned=date_earned,
                    expiry_date=expiry_date,
                    attachment_url=attachment_url
                )
                qualification.full_clean()
                qualification.save()
                return qualification
        except ValidationError as e:
            raise

    @staticmethod
    def get_qualification_by_id(qual_id: int) -> Optional[TeacherQualification]:
        try:
            return TeacherQualification.objects.get(id=qual_id)
        except TeacherQualification.DoesNotExist:
            return None

    @staticmethod
    def get_qualifications_by_teacher(teacher_id: int) -> List[TeacherQualification]:
        return TeacherQualification.objects.filter(teacher_id=teacher_id).order_by('-date_earned')

    @staticmethod
    def get_active_qualifications(teacher_id: int) -> List[TeacherQualification]:
        today = date.today()
        return TeacherQualification.objects.filter(
            teacher_id=teacher_id,
            expiry_date__gte=today
        ).order_by('-date_earned')

    @staticmethod
    def update_qualification(qualification: TeacherQualification, update_data: Dict[str, Any]) -> TeacherQualification:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(qualification, field):
                        setattr(qualification, field, value)
                qualification.full_clean()
                qualification.save()
                return qualification
        except ValidationError as e:
            raise

    @staticmethod
    def delete_qualification(qualification: TeacherQualification) -> bool:
        try:
            qualification.delete()
            return True
        except Exception:
            return False