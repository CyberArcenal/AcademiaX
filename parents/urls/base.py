from django.urls import path
from parents.views.parent import (
    ParentListView,
    ParentDetailView,
    ParentSearchView,
)

urlpatterns = [
    path("parents/", ParentListView.as_view(), name="parent-list"),
    path("parents/<int:parent_id>/", ParentDetailView.as_view(), name="parent-detail"),
    path("parents/search/", ParentSearchView.as_view(), name="parent-search"),
]

from parents.views.student_parent import (
    StudentParentListView,
    StudentParentDetailView,
)

urlpatterns += [
    path("student-parents/", StudentParentListView.as_view(), name="student-parent-list"),
    path("student-parents/<int:rel_id>/", StudentParentDetailView.as_view(), name="student-parent-detail"),
]


from parents.views.parent_communication import (
    ParentCommunicationLogListView,
    ParentCommunicationLogDetailView,
    ParentCommunicationLogResolveView,
)

urlpatterns += [
    path("parent-communications/", ParentCommunicationLogListView.as_view(), name="parent-communication-list"),
    path("parent-communications/<int:log_id>/", ParentCommunicationLogDetailView.as_view(), name="parent-communication-detail"),
    path("parent-communications/<int:log_id>/resolve/", ParentCommunicationLogResolveView.as_view(), name="parent-communication-resolve"),
]