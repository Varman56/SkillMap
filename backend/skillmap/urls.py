from django.conf import settings
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ИМПОРТИРУЙ СВОЮ НОВУЮ ФУНКЦИЮ СЮДА
# Судя по импортам, твоя папка называется api
from api.views.web_views import login_page

urlpatterns = [
    # REST API endpoints (оставляем как есть, чтобы не сломать старое)
    path("api/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # HTML Страницы Django Templates
    # Заменяем TemplateView для пустого пути и login на нашу функцию
    path("", login_page, name="index"),
    path("login/", login_page, name="login"),
    
    # Остальные страницы пока оставляем как есть, 
    # позже для них тоже нужно будет написать свои views
    path("profile/edit/", TemplateView.as_view(template_name="edit_profile.html"), name="edit_profile"),
    path("profile/", TemplateView.as_view(template_name="profile.html"), name="profile"),
    path("matrix/", TemplateView.as_view(template_name="matrix.html"), name="matrix"),
    path("hr/", TemplateView.as_view(template_name="hr.html"), name="hr"),
    path("ask/", TemplateView.as_view(template_name="ask.html"), name="ask"),
]