from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from classes.models.academic_year import AcademicYear
from classes.models.classroom import Classroom
from classes.models.grade_level import GradeLevel
from classes.models.section import Section
from classes.models.term import Term
from teachers.models.teacher import Teacher


class SectionService:
    """Service for Section model operations"""

    @staticmethod
    def create_section(
        name: str,
        grade_level: GradeLevel,
        academic_year: AcademicYear,
        homeroom_teacher: Optional[Teacher] = None,
        classroom: Optional[Classroom] = None,
        term: Optional[Term] = None,
        capacity: int = 40,
        is_active: bool = True
    ) -> Section:
        try:
            with transaction.atomic():
                section = Section(
                    name=name,
                    grade_level=grade_level,
                    academic_year=academic_year,
                    homeroom_teacher=homeroom_teacher,
                    classroom=classroom,
                    term=term,
                    capacity=capacity,
                    is_active=is_active
                )
                section.full_clean()
                section.save()
                return section
        except ValidationError as e:
            raise

    @staticmethod
    def get_section_by_id(section_id: int) -> Optional[Section]:
        try:
            return Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return None

    @staticmethod
    def get_sections_by_grade_level(grade_level_id: int, academic_year_id: int, active_only: bool = True) -> List[Section]:
        queryset = Section.objects.filter(grade_level_id=grade_level_id, academic_year_id=academic_year_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def get_sections_by_teacher(teacher_id: int, academic_year_id: int) -> List[Section]:
        return Section.objects.filter(
            homeroom_teacher_id=teacher_id,
            academic_year_id=academic_year_id
        )

    @staticmethod
    def update_section(section: Section, update_data: Dict[str, Any]) -> Section:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(section, field):
                        setattr(section, field, value)
                section.full_clean()
                section.save()
                return section
        except ValidationError as e:
            raise

    @staticmethod
    def delete_section(section: Section, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                section.is_active = False
                section.save()
            else:
                section.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def update_enrollment_count(section: Section) -> int:
        """Update current_enrollment based on active enrollments"""
        from enrollments.models import Enrollment
        count = Enrollment.objects.filter(
            section=section,
            status='ENR'
        ).count()
        section.current_enrollment = count
        section.save()
        return count

    @staticmethod
    def get_sections_with_availability(grade_level_id: int, academic_year_id: int) -> List[Dict]:
        """Return sections with remaining capacity"""
        sections = Section.objects.filter(
            grade_level_id=grade_level_id,
            academic_year_id=academic_year_id,
            is_active=True
        )
        result = []
        for section in sections:
            remaining = section.capacity - section.current_enrollment
            result.append({
                'id': section.id,
                'name': section.name,
                'capacity': section.capacity,
                'current_enrollment': section.current_enrollment,
                'remaining': remaining,
                'homeroom_teacher': str(section.homeroom_teacher) if section.homeroom_teacher else None
            })
        return result