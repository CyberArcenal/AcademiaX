from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.employee import Employee
from ..models.department import Department
from ..models.position import Position
from users.models import User
from common.enums.hr import EmploymentType, EmploymentStatus

class EmployeeService:
    """Service for Employee model operations"""

    @staticmethod
    def generate_employee_number() -> str:
        import random
        import string
        year = date.today().year
        random_digits = ''.join(random.choices(string.digits, k=6))
        return f"EMP-{year}-{random_digits}"

    @staticmethod
    def create_employee(
        user: User,
        hire_date: date,
        department: Optional[Department] = None,
        position: Optional[Position] = None,
        employment_type: str = EmploymentType.FULL_TIME,
        status: str = EmploymentStatus.ACTIVE,
        regularized_date: Optional[date] = None,
        supervisor: Optional[Employee] = None,
        contact_number: str = "",
        emergency_contact_name: str = "",
        emergency_contact_number: str = "",
        tin: str = "",
        sss: str = "",
        pagibig: str = "",
        philhealth: str = ""
    ) -> Employee:
        try:
            with transaction.atomic():
                employee = Employee(
                    user=user,
                    employee_number=EmployeeService.generate_employee_number(),
                    department=department,
                    position=position,
                    employment_type=employment_type,
                    status=status,
                    hire_date=hire_date,
                    regularized_date=regularized_date,
                    supervisor=supervisor,
                    contact_number=contact_number,
                    emergency_contact_name=emergency_contact_name,
                    emergency_contact_number=emergency_contact_number,
                    tin=tin,
                    sss=sss,
                    pagibig=pagibig,
                    philhealth=philhealth
                )
                employee.full_clean()
                employee.save()
                return employee
        except ValidationError as e:
            raise

    @staticmethod
    def get_employee_by_id(employee_id: int) -> Optional[Employee]:
        try:
            return Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return None

    @staticmethod
    def get_employee_by_user(user_id: int) -> Optional[Employee]:
        try:
            return Employee.objects.get(user_id=user_id)
        except Employee.DoesNotExist:
            return None

    @staticmethod
    def get_employee_by_number(employee_number: str) -> Optional[Employee]:
        try:
            return Employee.objects.get(employee_number=employee_number)
        except Employee.DoesNotExist:
            return None

    @staticmethod
    def get_employees_by_department(department_id: int, active_only: bool = True) -> List[Employee]:
        queryset = Employee.objects.filter(department_id=department_id)
        if active_only:
            queryset = queryset.filter(status=EmploymentStatus.ACTIVE)
        return queryset

    @staticmethod
    def update_employee(employee: Employee, update_data: Dict[str, Any]) -> Employee:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(employee, field):
                        setattr(employee, field, value)
                employee.full_clean()
                employee.save()
                return employee
        except ValidationError as e:
            raise

    @staticmethod
    def update_status(employee: Employee, status: str, resignation_date: Optional[date] = None) -> Employee:
        employee.status = status
        if status == EmploymentStatus.RESIGNED and resignation_date:
            employee.resignation_date = resignation_date
        employee.save()
        return employee

    @staticmethod
    def delete_employee(employee: Employee, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                employee.is_active = False
                employee.save()
            else:
                employee.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_employees(query: str, limit: int = 20) -> List[Employee]:
        from django.db import models
        return Employee.objects.filter(
            models.Q(user__first_name__icontains=query) |
            models.Q(user__last_name__icontains=query) |
            models.Q(employee_number__icontains=query)
        )[:limit]