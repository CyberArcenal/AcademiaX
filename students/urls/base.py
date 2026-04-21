from django.urls import path
from students.views.student import (
    StudentListView,
    StudentDetailView,
    StudentSearchView,
)

urlpatterns = [
    path("students/", StudentListView.as_view(), name="student-list"),
    path("students/<int:student_id>/", StudentDetailView.as_view(), name="student-detail"),
    path("students/search/", StudentSearchView.as_view(), name="student-search"),
]

from students.views.guardian import GuardianListView, GuardianDetailView

urlpatterns += [
    path("guardians/", GuardianListView.as_view(), name="guardian-list"),
    path("guardians/<int:guardian_id>/", GuardianDetailView.as_view(), name="guardian-detail"),
]

from students.views.medical_record import MedicalRecordListView, MedicalRecordDetailView

urlpatterns += [
    path("medical-records/", MedicalRecordListView.as_view(), name="medical-record-list"),
    path("medical-records/<int:record_id>/", MedicalRecordDetailView.as_view(), name="medical-record-detail"),
]

from students.views.student_document import (
    StudentDocumentListView,
    StudentDocumentDetailView,
    StudentDocumentVerifyView,
)

urlpatterns += [
    path("student-documents/", StudentDocumentListView.as_view(), name="student-document-list"),
    path("student-documents/<int:doc_id>/", StudentDocumentDetailView.as_view(), name="student-document-detail"),
    path("student-documents/<int:doc_id>/verify/", StudentDocumentVerifyView.as_view(), name="student-document-verify"),
]

from students.views.student_achievement import (
    StudentAchievementListView,
    StudentAchievementDetailView,
)

urlpatterns += [
    path("student-achievements/", StudentAchievementListView.as_view(), name="student-achievement-list"),
    path("student-achievements/<int:achievement_id>/", StudentAchievementDetailView.as_view(), name="student-achievement-detail"),
]