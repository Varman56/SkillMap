"""Сопоставление API-маршрутов на Django views."""
from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenRefreshView
 
from .views.ask import AskView
from .views.auth import LoginView, LogoutView, MeView
from .views.matrix import MatrixView
from .views.me import MyDashboardView, MySkillsListView
from .views.oauth import YandexCallbackView, YandexStartView
from .views.projects import (
    ProjectDetailView,
    ProjectMemberDetailView,
    ProjectMembersView,
    ProjectsListCreateView,
)
from .views.public_profiles import PublicProfileView
from .views.skills import (
    AllSkillsView,
    AvailableSkillsView,
    MySkillItemView,
    MySkillLevelView,
    MySkillsView,
)
from .views.users import UserDetailView, UsersListCreateView
 
TokenRefreshViewTagged = extend_schema(tags=["auth"])(TokenRefreshView)
 
urlpatterns = [
    # auth
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    path("auth/refresh", TokenRefreshViewTagged.as_view(), name="auth-refresh"),
 
    # Яндекс OAuth
    path("auth/yandex/start", YandexStartView.as_view(), name="auth-yandex-start"),
    path("auth/yandex/callback", YandexCallbackView.as_view(), name="auth-yandex-callback"),
 
    # users (HR)
    path("users", UsersListCreateView.as_view(), name="users"),
    path(
        "users/<int:user_id>",
        UserDetailView.as_view(),
        name="user-detail",
    ),
 
    # skills
    path("skills/available", AvailableSkillsView.as_view(), name="skills-available"),
    path("skills", AllSkillsView.as_view(), name="skills"),
    path("skills/my", MySkillsView.as_view(), name="skills-my"),
    path(
        "skills/my/<int:skill_id>",
        MySkillItemView.as_view(),
        name="skills-my-item",
    ),
    path(
        "skills/my/<int:skill_id>/level",
        MySkillLevelView.as_view(),
        name="skills-my-level",
    ),
 
    # me
    path("me/dashboard", MyDashboardView.as_view(), name="me-dashboard"),
    path("me/skills", MySkillsListView.as_view(), name="me-skills"),
 
    # matrix (HR/Manager)
    path("matrix", MatrixView.as_view(), name="matrix"),
 
    # projects
    path("projects", ProjectsListCreateView.as_view(), name="projects"),
    path(
        "projects/<int:project_id>",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "projects/<int:project_id>/members",
        ProjectMembersView.as_view(),
        name="project-members",
    ),
    path(
        "projects/<int:project_id>/members/<int:user_id>",
        ProjectMemberDetailView.as_view(),
        name="project-member-detail",
    ),
 
    # public profiles
    path(
        "public-profiles/<int:user_id>",
        PublicProfileView.as_view(),
        name="public-profile",
    ),
 
    # ask (search)
    path("ask", AskView.as_view(), name="ask"),
]
