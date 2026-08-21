from django.urls import path

from skillmap.views.web_views import login_page, logout_page
from skillmap.views.ask_page import ask_page
from skillmap.views.profile_page import profile_page
from skillmap.views.matrix_page import matrix_export, matrix_page
from skillmap.views.media_views import serve_photo, serve_resume
from skillmap.views.project_page import project_page
from skillmap.views.projects_page import projects_page
from skillmap.views.reserve_page import reserve_page
from skillmap.views.approvals_page import approvals_page
from skillmap.views.department_page import department_page

urlpatterns = [
    path("profile/", profile_page, name="my-profile"),
    path("profile/<int:user_id>/", profile_page, name="profile-page"),
    path("ask/", ask_page, name="ask-page"),
    # "projects/" (список) ДО "projects/<id>/" (карточка) — порядок не
    # обязателен (int-конвертер сам не даст "projects/" провалиться в
    # него), но так нагляднее: сначала общий список, потом конкретный.
    path("projects/", projects_page, name="projects-page"),
    path("projects/<int:project_id>/", project_page, name="project-page"),
    path("reserve/", reserve_page, name="reserve-page"),
    path("approvals/", approvals_page, name="approvals-page"),
    path("matrix/", matrix_page, name="matrix-page"),
    path("matrix/export/", matrix_export, name="matrix-export"),
    path("my-department/", department_page, name="my-department-page"),

    # Отдаём загруженные файлы (фото/резюме) из MEDIA_ROOT по префиксу
    # /media/ — раньше это был один общий django.views.static.serve БЕЗ
    # авторизации (см. media_views.py — фикс пункта 1.5 аудита: резюме
    # должен видеть только HR, а раньше это не проверялось вообще никем,
    # даже незалогиненным). Два разных view вместо одного catch-all —
    # у каждой подпапки своя проверка прав, см. media_views.py. Других
    # подпапок под MEDIA_ROOT в проекте нет (см. docstring там же).
    # Тоже должно стоять ДО spa-assets, иначе тот catch-all перехватит /media/*.jpg первым.
    path("media/photos/<path:path>", serve_photo, name="media-photo"),
    path("media/resumes/<path:path>", serve_resume, name="media-resume"),

    path("", login_page, name="index"),
    path("login/", login_page, name="login"),
    path("logout/", logout_page, name="logout"),
]
