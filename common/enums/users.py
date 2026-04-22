# common/enums/users.py
from django.db import models

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    ADMIN = 'ADMIN', 'Administrator'
    PRINCIPAL = 'PRINCIPAL', 'Principal'
    REGISTRAR = 'REGISTRAR', 'Registrar'
    TEACHER = 'TEACHER', 'Teacher'
    STUDENT = 'STUDENT', 'Student'
    PARENT = 'PARENT', 'Parent'
    STAFF = 'STAFF', 'Staff'
    ACCOUNTING = 'ACCOUNTING', 'Accounting'
    FACILITIES_MANAGER = 'FACILITIES_MANAGER', 'Facility Manager'
    LIBRARIAN = 'LIBRARIAN', 'Librarian'
    HR_MANAGER = 'HR_MANAGER', 'Hr Manager'

class AccountStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    PENDING = 'PENDING', 'Pending Verification'