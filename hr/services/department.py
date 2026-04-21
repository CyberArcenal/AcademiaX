from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.department import Department
from ..models.employee import Employee

class DepartmentService:
    """Service for Department model operations"""

    @staticmethod
    def create_department(
        name: str,
        code: str,
        description: str = "",
        head: Optional[Employee] = None,
        is_active: bool = True
    ) -> Department:
        try:
            with transaction.atomic():
                department = Department(
                    name=name,
                    code=code.upper(),
                    description=description,
                    head=head,
                    is_active=is_active
                )
                department.full_clean()
                department.save()
                return department
        except ValidationError as e:
            raise

    @staticmethod
    def get_department_by_id(dept_id: int) -> Optional[Department]:
        try:
            return Department.objects.get(id=dept_id)
        except Department.DoesNotExist:
            return None

    @staticmethod
    def get_department_by_code(code: str) -> Optional[Department]:
        try:
            return Department.objects.get(code=code.upper())
        except Department.DoesNotExist:
            return None

    @staticmethod
    def get_all_departments(active_only: bool = True) -> List[Department]:
        queryset = Department.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('name')

    @staticmethod
    def update_department(department: Department, update_data: Dict[str, Any]) -> Department:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(department, field):
                        if field == 'code':
                            value = value.upper()
                        setattr(department, field, value)
                department.full_clean()
                department.save()
                return department
        except ValidationError as e:
            raise

    @staticmethod
    def delete_department(department: Department, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                department.is_active = False
                department.save()
            else:
                department.delete()
            return True
        except Exception:
            return False