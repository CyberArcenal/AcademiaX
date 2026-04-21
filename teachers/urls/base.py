from django.urls import path
from teachers.views.teacher import (
    TeacherListView,
    TeacherDetailView,
    TeacherSearchView,
)

urlpatterns = [
    path("teachers/", TeacherListView.as_view(), name="teacher-list"),
    path("teachers/<int:teacher_id>/", TeacherDetailView.as_view(), name="teacher-detail"),
    path("teachers/search/", TeacherSearchView.as_view(), name="teacher-search"),
]

from teachers.views.specialization import (
    SpecializationListView,
    SpecializationDetailView,
)

urlpatterns += [
    path("specializations/", SpecializationListView.as_view(), name="specialization-list"),
    path("specializations/<int:spec_id>/", SpecializationDetailView.as_view(), name="specialization-detail"),
]

from teachers.views.teaching_assignment import (
    TeachingAssignmentListView,
    TeachingAssignmentDetailView,
    TeacherLoadView,
)

urlpatterns += [
    path("teaching-assignments/", TeachingAssignmentListView.as_view(), name="teaching-assignment-list"),
    path("teaching-assignments/<int:assignment_id>/", TeachingAssignmentDetailView.as_view(), name="teaching-assignment-detail"),
    path("teacher-load/", TeacherLoadView.as_view(), name="teacher-load"),
]

from teachers.views.teacher_qualification import (
    TeacherQualificationListView,
    TeacherQualificationDetailView,
)

urlpatterns += [
    path("teacher-qualifications/", TeacherQualificationListView.as_view(), name="teacher-qualification-list"),
    path("teacher-qualifications/<int:qual_id>/", TeacherQualificationDetailView.as_view(), name="teacher-qualification-detail"),
]