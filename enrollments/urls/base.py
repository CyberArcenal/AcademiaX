from django.urls import path
from enrollments.views.enrollment import (
    EnrollmentListView,
    EnrollmentDetailView,
    EnrollmentTransferSectionView,
)

urlpatterns = [
    path("enrollments/", EnrollmentListView.as_view(), name="enrollment-list"),
    path("enrollments/<int:enrollment_id>/", EnrollmentDetailView.as_view(), name="enrollment-detail"),
    path("enrollments/<int:enrollment_id>/transfer/", EnrollmentTransferSectionView.as_view(), name="enrollment-transfer"),
]

from enrollments.views.enrollment_history import (
    EnrollmentHistoryListView,
    EnrollmentHistoryDetailView,
)

urlpatterns += [
    path("enrollment-history/", EnrollmentHistoryListView.as_view(), name="enrollment-history-list"),
    path("enrollment-history/<int:history_id>/", EnrollmentHistoryDetailView.as_view(), name="enrollment-history-detail"),
]

from enrollments.views.subject_enrollment import (
    SubjectEnrollmentListView,
    SubjectEnrollmentDetailView,
    SubjectEnrollmentDropView,
)

urlpatterns += [
    path("subject-enrollments/", SubjectEnrollmentListView.as_view(), name="subject-enrollment-list"),
    path("subject-enrollments/<int:subject_enrollment_id>/", SubjectEnrollmentDetailView.as_view(), name="subject-enrollment-detail"),
    path("subject-enrollments/<int:subject_enrollment_id>/drop/", SubjectEnrollmentDropView.as_view(), name="subject-enrollment-drop"),
]

from enrollments.views.enrollment_hold import (
    EnrollmentHoldListView,
    EnrollmentHoldDetailView,
    EnrollmentHoldResolveView,
)

urlpatterns += [
    path("enrollment-holds/", EnrollmentHoldListView.as_view(), name="enrollment-hold-list"),
    path("enrollment-holds/<int:hold_id>/", EnrollmentHoldDetailView.as_view(), name="enrollment-hold-detail"),
    path("enrollment-holds/<int:hold_id>/resolve/", EnrollmentHoldResolveView.as_view(), name="enrollment-hold-resolve"),
]