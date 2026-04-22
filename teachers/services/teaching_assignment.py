from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.teaching_assignment import TeachingAssignment
from ..models.teacher import Teacher
from classes.models.section import Section
from academic.models.subject import Subject
from classes.models.academic_year import AcademicYear
from classes.models.term import Term

class TeachingAssignmentService:
    """Service for TeachingAssignment model operations"""

    @staticmethod
    def create_assignment(
        teacher: Teacher,
        section: Section,
        subject: Subject,
        academic_year: AcademicYear,
        term: Optional[Term] = None,
        is_active: bool = True
    ) -> TeachingAssignment:
        try:
            with transaction.atomic():
                # Check if assignment already exists
                existing = TeachingAssignment.objects.filter(
                    teacher=teacher,
                    section=section,
                    subject=subject,
                    academic_year=academic_year
                ).first()
                if existing:
                    raise ValidationError("Teaching assignment already exists")

                assignment = TeachingAssignment(
                    teacher=teacher,
                    section=section,
                    subject=subject,
                    academic_year=academic_year,
                    term=term,
                    is_active=is_active
                )
                assignment.full_clean()
                assignment.save()
                return assignment
        except ValidationError as e:
            raise

    @staticmethod
    def get_assignment_by_id(assignment_id: int) -> Optional[TeachingAssignment]:
        try:
            return TeachingAssignment.objects.get(id=assignment_id)
        except TeachingAssignment.DoesNotExist:
            return None

    @staticmethod
    def get_assignments_by_teacher(teacher_id: int, academic_year_id: Optional[int] = None) -> List[TeachingAssignment]:
        queryset = TeachingAssignment.objects.filter(teacher_id=teacher_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.select_related('section', 'subject')

    @staticmethod
    def get_assignments_by_section(section_id: int, academic_year_id: Optional[int] = None) -> List[TeachingAssignment]:
        queryset = TeachingAssignment.objects.filter(section_id=section_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.select_related('teacher', 'subject')

    @staticmethod
    def get_assignments_by_subject(subject_id: int, academic_year_id: Optional[int] = None) -> List[TeachingAssignment]:
        queryset = TeachingAssignment.objects.filter(subject_id=subject_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.select_related('teacher', 'section')

    @staticmethod
    def update_assignment(assignment: TeachingAssignment, update_data: Dict[str, Any]) -> TeachingAssignment:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(assignment, field):
                        setattr(assignment, field, value)
                assignment.full_clean()
                assignment.save()
                return assignment
        except ValidationError as e:
            raise

    @staticmethod
    def delete_assignment(assignment: TeachingAssignment) -> bool:
        try:
            assignment.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_teacher_load(teacher_id: int, academic_year_id: int) -> Dict:
        """Get teacher's load summary (number of assignments, subjects, sections)"""
        assignments = TeachingAssignment.objects.filter(teacher_id=teacher_id, academic_year_id=academic_year_id)
        return {
            'total_assignments': assignments.count(),
            'unique_subjects': assignments.values('subject_id').distinct().count(),
            'unique_sections': assignments.values('section_id').distinct().count(),
        }