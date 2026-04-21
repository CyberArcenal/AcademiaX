from django.urls import path
from attendance.views.student_attendance import (
    StudentAttendanceListView,
    StudentAttendanceDetailView,
    BulkAttendanceMarkView,
)

urlpatterns = [
    path("student-attendances/", StudentAttendanceListView.as_view(), name="student-attendance-list"),
    path("student-attendances/<int:attendance_id>/", StudentAttendanceDetailView.as_view(), name="student-attendance-detail"),
    path("student-attendances/bulk/", BulkAttendanceMarkView.as_view(), name="student-attendance-bulk"),
]

from attendance.views.teacher_attendance import (
    TeacherAttendanceListView,
    TeacherAttendanceDetailView,
)

urlpatterns += [
    path("teacher-attendances/", TeacherAttendanceListView.as_view(), name="teacher-attendance-list"),
    path("teacher-attendances/<int:attendance_id>/", TeacherAttendanceDetailView.as_view(), name="teacher-attendance-detail"),
]

from attendance.views.holiday import (
    HolidayListView,
    HolidayDetailView,
    HolidayCheckView,
)

urlpatterns += [
    path("holidays/", HolidayListView.as_view(), name="holiday-list"),
    path("holidays/<int:holiday_id>/", HolidayDetailView.as_view(), name="holiday-detail"),
    path("holidays/check/", HolidayCheckView.as_view(), name="holiday-check"),
]


from attendance.views.attendance_summary import (
    StudentAttendanceSummaryListView,
    StudentAttendanceSummaryDetailView,
    StudentAttendanceSummaryRecalculateView,
)

urlpatterns += [
    path("attendance-summaries/", StudentAttendanceSummaryListView.as_view(), name="summary-list"),
    path("attendance-summaries/<int:summary_id>/", StudentAttendanceSummaryDetailView.as_view(), name="summary-detail"),
    path("attendance-summaries/<int:summary_id>/recalculate/", StudentAttendanceSummaryRecalculateView.as_view(), name="summary-recalculate"),
]