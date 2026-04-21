from django.urls import path
from hr.views.department import DepartmentListView, DepartmentDetailView

urlpatterns = [
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("departments/<int:dept_id>/", DepartmentDetailView.as_view(), name="department-detail"),
]

from hr.views.position import PositionListView, PositionDetailView

urlpatterns += [
    path("positions/", PositionListView.as_view(), name="position-list"),
    path("positions/<int:position_id>/", PositionDetailView.as_view(), name="position-detail"),
]

from hr.views.employee import (
    EmployeeListView,
    EmployeeDetailView,
    EmployeeSearchView,
)

urlpatterns += [
    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    path("employees/<int:employee_id>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("employees/search/", EmployeeSearchView.as_view(), name="employee-search"),
]

from hr.views.leave import (
    LeaveRequestListView,
    LeaveRequestDetailView,
    LeaveRequestApproveView,
    LeaveRequestRejectView,
)

urlpatterns += [
    path("leave-requests/", LeaveRequestListView.as_view(), name="leave-list"),
    path("leave-requests/<int:leave_id>/", LeaveRequestDetailView.as_view(), name="leave-detail"),
    path("leave-requests/<int:leave_id>/approve/", LeaveRequestApproveView.as_view(), name="leave-approve"),
    path("leave-requests/<int:leave_id>/reject/", LeaveRequestRejectView.as_view(), name="leave-reject"),
]

from hr.views.attendance import (
    EmployeeAttendanceListView,
    EmployeeAttendanceDetailView,
)

urlpatterns += [
    path("employee-attendances/", EmployeeAttendanceListView.as_view(), name="employee-attendance-list"),
    path("employee-attendances/<int:attendance_id>/", EmployeeAttendanceDetailView.as_view(), name="employee-attendance-detail"),
]

from hr.views.payroll import (
    SalaryGradeListView,
    SalaryGradeDetailView,
    PayrollPeriodListView,
    PayrollPeriodDetailView,
    PayrollPeriodCloseView,
    CurrentPayrollPeriodView,
)

urlpatterns += [
    path("salary-grades/", SalaryGradeListView.as_view(), name="salary-grade-list"),
    path("salary-grades/<int:grade_id>/", SalaryGradeDetailView.as_view(), name="salary-grade-detail"),
    path("payroll-periods/", PayrollPeriodListView.as_view(), name="payroll-period-list"),
    path("payroll-periods/<int:period_id>/", PayrollPeriodDetailView.as_view(), name="payroll-period-detail"),
    path("payroll-periods/<int:period_id>/close/", PayrollPeriodCloseView.as_view(), name="payroll-period-close"),
    path("payroll-periods/current/", CurrentPayrollPeriodView.as_view(), name="current-payroll-period"),
]

from hr.views.payslip import (
    PayslipListView,
    PayslipDetailView,
    PayslipMarkPaidView,
)

urlpatterns += [
    path("payslips/", PayslipListView.as_view(), name="payslip-list"),
    path("payslips/<int:payslip_id>/", PayslipDetailView.as_view(), name="payslip-detail"),
    path("payslips/<int:payslip_id>/mark-paid/", PayslipMarkPaidView.as_view(), name="payslip-mark-paid"),
]