from django.urls import path
from alumni.views.alumni import AlumniListView, AlumniDetailView, AlumniSearchView

urlpatterns = [
    path("alumni/", AlumniListView.as_view(), name="alumni-list"),
    path("alumni/<int:alumni_id>/", AlumniDetailView.as_view(), name="alumni-detail"),
    path("alumni/search/", AlumniSearchView.as_view(), name="alumni-search"),
]

from alumni.views.employment import EmploymentListView, EmploymentDetailView

urlpatterns += [
    path("employments/", EmploymentListView.as_view(), name="employment-list"),
    path("employments/<int:employment_id>/", EmploymentDetailView.as_view(), name="employment-detail"),
]

from alumni.views.education import EducationListView, EducationDetailView

urlpatterns += [
    path("educations/", EducationListView.as_view(), name="education-list"),
    path("educations/<int:education_id>/", EducationDetailView.as_view(), name="education-detail"),
]

from alumni.views.donation import DonationListView, DonationDetailView, DonationStatisticsView

urlpatterns += [
    path("donations/", DonationListView.as_view(), name="donation-list"),
    path("donations/<int:donation_id>/", DonationDetailView.as_view(), name="donation-detail"),
    path("donations/statistics/", DonationStatisticsView.as_view(), name="donation-statistics"),
]

from alumni.views.event import (
    AlumniEventListView,
    AlumniEventDetailView,
    EventAttendanceListView,
    EventAttendanceDetailView,
    EventAttendanceCheckinView,
)

urlpatterns += [
    path("events/", AlumniEventListView.as_view(), name="event-list"),
    path("events/<int:event_id>/", AlumniEventDetailView.as_view(), name="event-detail"),
    path("event-attendances/", EventAttendanceListView.as_view(), name="attendance-list"),
    path("event-attendances/<int:attendance_id>/", EventAttendanceDetailView.as_view(), name="attendance-detail"),
    path("event-attendances/<int:attendance_id>/checkin/", EventAttendanceCheckinView.as_view(), name="attendance-checkin"),
]

from alumni.views.achievement import AchievementListView, AchievementDetailView

urlpatterns += [
    path("achievements/", AchievementListView.as_view(), name="achievement-list"),
    path("achievements/<int:achievement_id>/", AchievementDetailView.as_view(), name="achievement-detail"),
]