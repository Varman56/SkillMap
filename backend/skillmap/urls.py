from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from skillmap.views.web_views import login_page, logout_page
from skillmap.views.ask_page import ask_page
from skillmap.views.profile_page import profile_page
from skillmap.views.matrix_page import matrix_export, matrix_page
from skillmap.views.project_page import project_page
from skillmap.views.reserve_page import reserve_page
from skillmap.views.approvals_page import approvals_page
from skillmap.views.department_page import department_page

urlpatterns = [
    path("profile/", profile_page, name="my-profile"),
    path("profile/<int:user_id>/", profile_page, name="profile-page"),
    path("ask/", ask_page, name="ask-page"),
    path("projects/<int:project_id>/", project_page, name="project-page"),
    path("reserve/", reserve_page, name="reserve-page"),
    path("approvals/", approvals_page, name="approvals-page"),
    path("matrix/", matrix_page, name="matrix-page"),
    path("matrix/export/", matrix_export, name="matrix-export"),
    path("my-department/", department_page, name="my-department-page"),

    # Отдаём загруженные файлы (фото/резюме) из MEDIA_ROOT по префиксу /media/.
    # Тоже должно стоять ДО spa-assets, иначе тот catch-all перехватит /media/*.jpg первым.
    re_path(
        r"^media/(?P<path>.+)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
        name="media",
    ),

    path("", login_page, name="index"),
    path("login/", login_page, name="login"),
    path("logout/", logout_page, name="logout"),
]
