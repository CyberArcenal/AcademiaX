from django.urls import path
from academic.views.subject import SubjectListView, SubjectDetailView, SubjectSearchView
# Import other views as we create them

urlpatterns = [
    path("subjects/", SubjectListView.as_view(), name="subject-list"),
    path("subjects/<int:subject_id>/", SubjectDetailView.as_view(), name="subject-detail"),
    path("subjects/search/", SubjectSearchView.as_view(), name="subject-search"),
]

from academic.views.curriculum import CurriculumListView, CurriculumDetailView

urlpatterns += [
    path("curricula/", CurriculumListView.as_view(), name="curriculum-list"),
    path("curricula/<int:curriculum_id>/", CurriculumDetailView.as_view(), name="curriculum-detail"),
]

from academic.views.curriculum_subject import (
    CurriculumSubjectListView,
    CurriculumSubjectDetailView,
    CurriculumSubjectReorderView,
)

urlpatterns += [
    path("curriculum-subjects/", CurriculumSubjectListView.as_view(), name="curriculum-subject-list"),
    path("curriculum-subjects/<int:cs_id>/", CurriculumSubjectDetailView.as_view(), name="curriculum-subject-detail"),
    path("curricula/<int:curriculum_id>/reorder/", CurriculumSubjectReorderView.as_view(), name="curriculum-subject-reorder"),
]

from academic.views.learning_outcome import (
    LearningOutcomeListView,
    LearningOutcomeDetailView,
    LearningOutcomeReorderView,
)

urlpatterns += [
    path("learning-outcomes/", LearningOutcomeListView.as_view(), name="learning-outcome-list"),
    path("learning-outcomes/<int:outcome_id>/", LearningOutcomeDetailView.as_view(), name="learning-outcome-detail"),
    path("subjects/<int:subject_id>/learning-outcomes/reorder/", LearningOutcomeReorderView.as_view(), name="learning-outcome-reorder"),
]

from academic.views.prerequisite import (
    PrerequisiteListView,
    PrerequisiteDetailView,
    PrerequisiteCheckView,
)

urlpatterns += [
    path("prerequisites/", PrerequisiteListView.as_view(), name="prerequisite-list"),
    path("prerequisites/<int:prereq_id>/", PrerequisiteDetailView.as_view(), name="prerequisite-detail"),
    path("subjects/<int:subject_id>/check-prerequisites/", PrerequisiteCheckView.as_view(), name="prerequisite-check"),
]