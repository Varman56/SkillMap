from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from api.views.web_views import login_page, logout_page
from api.views.ask_page import ask_page
from api.views.profile_page import profile_page
from api.views.matrix_page import matrix_page
from api.views.project_page import project_page
from api.views.reserve_page import reserve_page
from api.views.approvals_page import approvals_page

urlpatterns = [
    path("api/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    path("profile/", profile_page, name="my-profile"),
    path("profile/<int:user_id>/", profile_page, name="profile-page"),
    path("ask/", ask_page, name="ask-page"),
    path("projects/<int:project_id>/", project_page, name="project-page"),
    path("reserve/", reserve_page, name="reserve-page"),
    path("approvals/", approvals_page, name="approvals-page"),
    # Отдаём загруженные файлы (фото/резюме) из MEDIA_ROOT по префиксу /media/.
    # Тоже должно стоять ДО spa-assets, иначе тот catch-all перехватит /media/*.jpg первым.
    re_path(
        r"^media/(?P<path>.+)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
        name="media",
    ),

    # HTML Страницы Django Templates
    # Заменяем TemplateView для пустого пути и login на нашу функцию
    path("", login_page, name="index"),
    path("login/", login_page, name="login"),
    path("logout/", logout_page, name="logout"),

    # Остальные страницы пока оставляем как есть,
    # позже для них тоже нужно будет написать свои views
    # path("profile/edit/", TemplateView.as_view(template_name="edit_profile.html"), name="edit_profile"),
    path("matrix/", matrix_page, name="matrix"),
    # path("hr/", TemplateView.as_view(template_name="hr.html"), name="hr"),
    # path("ask/", TemplateView.as_view(template_name="ask.html"), name="ask"),
]
