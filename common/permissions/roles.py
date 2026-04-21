from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from common.enums.users import AccountStatus, UserRole

User = get_user_model()


class BaseRolePermission(permissions.BasePermission):
    """Base class for role-based permissions"""
    message = _("You do not have permission to perform this action.")
    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role in self.allowed_roles


class IsAdmin(BaseRolePermission):
    allowed_roles = [UserRole.ADMIN]


class IsRegistrar(BaseRolePermission):
    allowed_roles = [UserRole.REGISTRAR]


class IsTeacher(BaseRolePermission):
    allowed_roles = [UserRole.TEACHER]


class IsStudent(BaseRolePermission):
    allowed_roles = [UserRole.STUDENT]


class IsParent(BaseRolePermission):
    allowed_roles = [UserRole.PARENT]


class IsStaff(BaseRolePermission):
    allowed_roles = [UserRole.STAFF, UserRole.ADMIN, UserRole.REGISTRAR]


class IsAccounting(BaseRolePermission):
    allowed_roles = [UserRole.ACCOUNTING]


class IsFacilitiesManager(BaseRolePermission):
    allowed_roles = [UserRole.FACILITIES_MANAGER]


class IsLibrarian(BaseRolePermission):
    allowed_roles = [UserRole.LIBRARIAN]


class IsHrManager(BaseRolePermission):
    allowed_roles = [UserRole.HR_MANAGER]


class IsAdminOrRegistrar(BaseRolePermission):
    allowed_roles = [UserRole.ADMIN, UserRole.REGISTRAR]


class IsAdminOrAccounting(BaseRolePermission):
    allowed_roles = [UserRole.ADMIN, UserRole.ACCOUNTING]


class IsStaffOrAdmin(BaseRolePermission):
    allowed_roles = [UserRole.STAFF, UserRole.ADMIN]


class IsAccountActive(permissions.BasePermission):
    """Allows access only to users whose status is ACTIVE"""
    message = _("Your account is not active.")

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.status == AccountStatus.ACTIVE


# ----------------------------------------------------------------------
# Helper functions for view-level permission checks
# ----------------------------------------------------------------------

def is_admin(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.ADMIN


def is_registrar(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.REGISTRAR


def is_teacher(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.TEACHER


def is_student(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.STUDENT


def is_parent(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.PARENT


def is_accounting(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.ACCOUNTING


def is_facilities_manager(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.FACILITIES_MANAGER


def is_librarian(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.LIBRARIAN


def is_hr_manager(user) -> bool:
    if not isinstance(user, User):
        return False
    return user.role == UserRole.HR_MANAGER


def is_staff(user) -> bool:
    """Returns True if user has staff-level permissions (admin, registrar, staff)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.REGISTRAR, UserRole.STAFF]


def can_edit(user) -> bool:
    """Check if user can edit resources (admin, registrar, staff)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.REGISTRAR, UserRole.STAFF]


def can_approve(user) -> bool:
    """Check if user can approve requests (admin, registrar)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.REGISTRAR]


def can_create(user) -> bool:
    """Check if user can create resources (admin, registrar, staff)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.REGISTRAR, UserRole.STAFF]


def can_read(user) -> bool:
    """Check if user can read resources (authenticated users with active status)."""
    if not isinstance(user, User):
        return False
    return user.is_authenticated and user.status == AccountStatus.ACTIVE


def can_delete(user) -> bool:
    """Check if user can delete resources (admin only)."""
    if not isinstance(user, User):
        return False
    return user.role == UserRole.ADMIN


def can_confirm(user) -> bool:
    """Check if user can confirm payments/transactions (admin, accounting)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.ACCOUNTING]


def can_receive(user) -> bool:
    """Check if user can mark orders as received (admin, staff)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.STAFF]


def can_cancel(user) -> bool:
    """Check if user can cancel orders/requests (admin, registrar)."""
    if not isinstance(user, User):
        return False
    return user.role in [UserRole.ADMIN, UserRole.REGISTRAR]