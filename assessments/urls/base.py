from django.urls import path
from assessments.views.assessment import (
    AssessmentListView,
    AssessmentDetailView,
    AssessmentPublishView,
)

urlpatterns = [
    path("assessments/", AssessmentListView.as_view(), name="assessment-list"),
    path("assessments/<int:assessment_id>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("assessments/<int:assessment_id>/publish/", AssessmentPublishView.as_view(), name="assessment-publish"),
]

from assessments.views.question import (
    QuestionListView,
    QuestionDetailView,
    QuestionReorderView,
)

urlpatterns += [
    path("questions/", QuestionListView.as_view(), name="question-list"),
    path("questions/<int:question_id>/", QuestionDetailView.as_view(), name="question-detail"),
    path("assessments/<int:assessment_id>/questions/reorder/", QuestionReorderView.as_view(), name="question-reorder"),
]

from assessments.views.choice import (
    ChoiceListView,
    ChoiceDetailView,
    BulkChoiceCreateView,
)

urlpatterns += [
    path("choices/", ChoiceListView.as_view(), name="choice-list"),
    path("choices/<int:choice_id>/", ChoiceDetailView.as_view(), name="choice-detail"),
    path("questions/<int:question_id>/choices/bulk/", BulkChoiceCreateView.as_view(), name="choice-bulk-create"),
]

from assessments.views.submission import (
    SubmissionListView,
    SubmissionDetailView,
    SubmissionGradeView,
)

urlpatterns += [
    path("submissions/", SubmissionListView.as_view(), name="submission-list"),
    path("submissions/<int:submission_id>/", SubmissionDetailView.as_view(), name="submission-detail"),
    path("submissions/<int:submission_id>/grade/", SubmissionGradeView.as_view(), name="submission-grade"),
]

from assessments.views.answer import (
    AnswerListView,
    AnswerDetailView,
    AnswerGradeView,
)

urlpatterns += [
    path("answers/", AnswerListView.as_view(), name="answer-list"),
    path("answers/<int:answer_id>/", AnswerDetailView.as_view(), name="answer-detail"),
    path("answers/<int:answer_id>/grade/", AnswerGradeView.as_view(), name="answer-grade"),
]

from assessments.views.rubric import (
    RubricCriterionListView,
    RubricCriterionDetailView,
    RubricLevelListView,
    RubricLevelDetailView,
)

urlpatterns += [
    path("rubric-criteria/", RubricCriterionListView.as_view(), name="criterion-list"),
    path("rubric-criteria/<int:criterion_id>/", RubricCriterionDetailView.as_view(), name="criterion-detail"),
    path("rubric-levels/", RubricLevelListView.as_view(), name="level-list"),
    path("rubric-levels/<int:level_id>/", RubricLevelDetailView.as_view(), name="level-detail"),
]

from assessments.views.grade import (
    AssessmentGradeListView,
    AssessmentGradeDetailView,
)

urlpatterns += [
    path("grades/", AssessmentGradeListView.as_view(), name="grade-list"),
    path("grades/<int:grade_id>/", AssessmentGradeDetailView.as_view(), name="grade-detail"),
]