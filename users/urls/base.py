import django
from django.urls import include, path
from users.views.user import (
    UserListView,
    UserDetailView,
    UserSearchView,
    UserMeView,
    UserChangePasswordView,
)
from users.views.user_log import UserLogListView
from .login import urlpatterns as login_urlpatterns
from .login_checkpoint import urlpatterns as checkpoint
from .password_reset import urlpatterns as password_urlpatterns


urlpatterns = [
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("users/search/", UserSearchView.as_view(), name="user-search"),
    path("users/me/", UserMeView.as_view(), name="user-me"),
    path("users/me/change-password/", UserChangePasswordView.as_view(), name="user-change-password"),
    path("user-logs/", UserLogListView.as_view(), name="user-log-list"),
]

urlpatterns += [
    path("auth/", include(login_urlpatterns)),
    path("password/", include(password_urlpatterns)),
    path("auth-checkpoints/", include(checkpoint)),
]