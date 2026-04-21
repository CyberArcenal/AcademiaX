from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import models
from typing import Optional, List, Dict, Any

from ..models.academic_program import AcademicProgram
from ...common.enums.academic import CurriculumLevel

class AcademicProgramService:
    """Service for AcademicProgram model operations"""

    @staticmethod
    def create_program(
        code: str,
        name: str,
        level: str,
        description: str = "",
        is_active: bool = True
    ) -> AcademicProgram:
        try:
            with transaction.atomic():
                program = AcademicProgram(
                    code=code.upper(),
                    name=name.title(),
                    level=level,
                    description=description,
                    is_active=is_active
                )
                program.full_clean()
                program.save()
                return program
        except ValidationError as e:
            raise

    @staticmethod
    def get_program_by_id(program_id: int) -> Optional[AcademicProgram]:
        try:
            return AcademicProgram.objects.get(id=program_id)
        except AcademicProgram.DoesNotExist:
            return None

    @staticmethod
    def get_program_by_code(code: str) -> Optional[AcademicProgram]:
        try:
            return AcademicProgram.objects.get(code=code.upper())
        except AcademicProgram.DoesNotExist:
            return None

    @staticmethod
    def get_all_programs(active_only: bool = True) -> List[AcademicProgram]:
        queryset = AcademicProgram.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def update_program(program: AcademicProgram, update_data: Dict[str, Any]) -> AcademicProgram:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(program, field):
                        if field == 'code':
                            value = value.upper()
                        elif field == 'name':
                            value = value.title()
                        setattr(program, field, value)
                program.full_clean()
                program.save()
                return program
        except ValidationError as e:
            raise

    @staticmethod
    def delete_program(program: AcademicProgram, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                program.is_active = False
                program.save()
            else:
                program.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_programs_by_level(level: str) -> List[AcademicProgram]:
        return AcademicProgram.objects.filter(level=level, is_active=True)