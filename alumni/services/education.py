from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.education import PostGraduateEducation
from ..models.alumni import Alumni

class PostGraduateEducationService:
    """Service for PostGraduateEducation model operations"""

    @staticmethod
    def create_education(
        alumni: Alumni,
        degree: str,
        institution: str,
        year_start: int,
        year_end: Optional[int] = None,
        is_graduate: bool = True,
        notes: str = ""
    ) -> PostGraduateEducation:
        try:
            with transaction.atomic():
                education = PostGraduateEducation(
                    alumni=alumni,
                    degree=degree.title(),
                    institution=institution.title(),
                    year_start=year_start,
                    year_end=year_end,
                    is_graduate=is_graduate,
                    notes=notes
                )
                education.full_clean()
                education.save()
                return education
        except ValidationError as e:
            raise

    @staticmethod
    def get_education_by_id(education_id: int) -> Optional[PostGraduateEducation]:
        try:
            return PostGraduateEducation.objects.get(id=education_id)
        except PostGraduateEducation.DoesNotExist:
            return None

    @staticmethod
    def get_educations_by_alumni(alumni_id: int) -> List[PostGraduateEducation]:
        return PostGraduateEducation.objects.filter(alumni_id=alumni_id).order_by('-year_end')

    @staticmethod
    def update_education(education: PostGraduateEducation, update_data: Dict[str, Any]) -> PostGraduateEducation:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(education, field):
                        if field in ['degree', 'institution']:
                            value = value.title()
                        setattr(education, field, value)
                education.full_clean()
                education.save()
                return education
        except ValidationError as e:
            raise

    @staticmethod
    def delete_education(education: PostGraduateEducation) -> bool:
        try:
            education.delete()
            return True
        except Exception:
            return False