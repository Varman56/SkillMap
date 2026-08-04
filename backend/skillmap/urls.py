from django.conf import settings
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from api.views.web_views import login_page
from api.views.profile_page import profile_page
from api.views.matrix_page import matrix_page_data

urlpatterns = [
    path("api/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Отдельная HTML-страница профиля (не API, обычный Django-темплейт).
    # Должна стоять ДО catch-all'ов SPA ниже, иначе их re_path перехватит путь первым.
    path("profile/<int:user_id>/", profile_page, name="profile-page"),
    # Отдаём загруженные файлы (фото/резюме) из MEDIA_ROOT по префиксу /media/.
    # Тоже должно стоять ДО spa-assets, иначе тот catch-all перехватит /media/*.jpg первым.
    # JSON-данные для SPA-страницы "Матрица компетенций" (не HTML, не DRF-ручка).
    # Тоже должно стоять ДО catch-all'ов ниже.
    path("matrix-data/", matrix_page_data, name="matrix-data"),
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

    # Остальные страницы пока оставляем как есть,
    # позже для них тоже нужно будет написать свои views
    # path("profile/edit/", TemplateView.as_view(template_name="edit_profile.html"), name="edit_profile"),
    path("matrix/", TemplateView.as_view(template_name="matrix.html"), name="matrix"),
    path("hr/", TemplateView.as_view(template_name="hr.html"), name="hr"),
    path("ask/", TemplateView.as_view(template_name="ask.html"), name="ask"),
]