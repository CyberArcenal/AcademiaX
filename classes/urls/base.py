from django.urls import path
from classes.views.academic_year import (
    AcademicYearListView,
    AcademicYearDetailView,
    AcademicYearSetCurrentView,
)

urlpatterns = [
    path("academic-years/", AcademicYearListView.as_view(), name="academic-year-list"),
    path("academic-years/<int:year_id>/", AcademicYearDetailView.as_view(), name="academic-year-detail"),
    path("academic-years/<int:year_id>/set-current/", AcademicYearSetCurrentView.as_view(), name="academic-year-set-current"),
]

from classes.views.classroom import (
    ClassroomListView,
    ClassroomDetailView,
    ClassroomAvailabilityView,
)

urlpatterns += [
    path("classrooms/", ClassroomListView.as_view(), name="classroom-list"),
    path("classrooms/<int:classroom_id>/", ClassroomDetailView.as_view(), name="classroom-detail"),
    path("classrooms/availability/", ClassroomAvailabilityView.as_view(), name="classroom-availability"),
]

from classes.views.section import (
    SectionListView,
    SectionDetailView,
    SectionAvailabilityView,
    SectionUpdateEnrollmentCountView,
)

urlpatterns += [
    path("sections/", SectionListView.as_view(), name="section-list"),
    path("sections/<int:section_id>/", SectionDetailView.as_view(), name="section-detail"),
    path("sections/availability/", SectionAvailabilityView.as_view(), name="section-availability"),
    path("sections/<int:section_id>/update-enrollment/", SectionUpdateEnrollmentCountView.as_view(), name="section-update-enrollment"),
]

from classes.views.term import (
    TermListView,
    TermDetailView,
    TermActivateView,
    TermDeactivateView,
    CurrentTermView,
)

urlpatterns += [
    path("terms/", TermListView.as_view(), name="term-list"),
    path("terms/<int:term_id>/", TermDetailView.as_view(), name="term-detail"),
    path("terms/<int:term_id>/activate/", TermActivateView.as_view(), name="term-activate"),
    path("terms/<int:term_id>/deactivate/", TermDeactivateView.as_view(), name="term-deactivate"),
    path("terms/current/", CurrentTermView.as_view(), name="current-term"),
]

from classes.views.grade_level import (
    GradeLevelListView,
    GradeLevelDetailView,
    GradeLevelReorderView,
)

urlpatterns += [
    path("grade-levels/", GradeLevelListView.as_view(), name="grade-level-list"),
    path("grade-levels/<int:grade_level_id>/", GradeLevelDetailView.as_view(), name="grade-level-detail"),
    path("grade-levels/reorder/", GradeLevelReorderView.as_view(), name="grade-level-reorder"),
]