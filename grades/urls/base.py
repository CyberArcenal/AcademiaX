from django.urls import path
from grades.views.grade import (
    GradeListView,
    GradeDetailView,
    GradeSubmitView,
    GradeApproveView,
)

urlpatterns = [
    path("grades/", GradeListView.as_view(), name="grade-list"),
    path("grades/<int:grade_id>/", GradeDetailView.as_view(), name="grade-detail"),
    path("grades/<int:grade_id>/submit/", GradeSubmitView.as_view(), name="grade-submit"),
    path("grades/<int:grade_id>/approve/", GradeApproveView.as_view(), name="grade-approve"),
]

from grades.views.grade_component import (
    GradeComponentListView,
    GradeComponentDetailView,
    GradeComponentValidateWeightsView,
)

urlpatterns += [
    path("grade-components/", GradeComponentListView.as_view(), name="grade-component-list"),
    path("grade-components/<int:component_id>/", GradeComponentDetailView.as_view(), name="grade-component-detail"),
    path("grade-components/validate-weights/", GradeComponentValidateWeightsView.as_view(), name="grade-component-validate"),
]

from grades.views.final_grade import (
    FinalGradeListView,
    FinalGradeDetailView,
    FinalGradeComputeView,
)

urlpatterns += [
    path("final-grades/", FinalGradeListView.as_view(), name="final-grade-list"),
    path("final-grades/<int:final_id>/", FinalGradeDetailView.as_view(), name="final-grade-detail"),
    path("final-grades/<int:final_id>/compute/", FinalGradeComputeView.as_view(), name="final-grade-compute"),
]

from grades.views.report_card import (
    ReportCardListView,
    ReportCardDetailView,
    ReportCardComputeGPAView,
)

urlpatterns += [
    path("report-cards/", ReportCardListView.as_view(), name="report-card-list"),
    path("report-cards/<int:report_id>/", ReportCardDetailView.as_view(), name="report-card-detail"),
    path("report-cards/<int:report_id>/compute-gpa/", ReportCardComputeGPAView.as_view(), name="report-card-compute-gpa"),
]

from grades.views.transcript import (
    TranscriptListView,
    TranscriptDetailView,
    TranscriptComputeGWAView,
    TranscriptMarkOfficialView,
)

urlpatterns += [
    path("transcripts/", TranscriptListView.as_view(), name="transcript-list"),
    path("transcripts/<int:transcript_id>/", TranscriptDetailView.as_view(), name="transcript-detail"),
    path("transcripts/<int:transcript_id>/compute-gwa/", TranscriptComputeGWAView.as_view(), name="transcript-compute-gwa"),
    path("transcripts/<int:transcript_id>/mark-official/", TranscriptMarkOfficialView.as_view(), name="transcript-mark-official"),
]