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
    path("profile/edit/", TemplateView.as_view(template_name="edit_profile.html", extra_context ={
        'skills': [
            {'level_class': 'expert', 'level_name': 'Эксперт', 'name': 'Работа с диаграммами (Miro)'},
            {'level_class': 'advanced', 'level_name': 'Продвинутый', 'name': 'Работа с Figma'},
            {'level_class': 'advanced', 'level_name': 'Продвинутый', 'name': 'Работа с Webflow'},
            {'level_class': 'novice', 'level_name': 'Новичок', 'name': 'Базы данных (Redis)'},
            {'level_class': 'novice', 'level_name': 'Новичок', 'name': 'Базы данных (MySQL)'},
            {'level_class': 'experienced', 'level_name': 'Опытный', 'name': 'Языки программирования (Python)'},
            {'level_class': 'novice', 'level_name': 'Новичок', 'name': 'Языки программирования (Golang)'},
        ],
        'projects': [
            {
                'id': 1, 
                'icon': 'Component-1.svg', 
                'title': 'Платформа деплоя', 
                'description': 'Разработка макетов платформы для автоматического деплоя сервисов'
            },
            {
                'id': 2, 
                'icon': 'Component-2.svg', 
                'title': 'Веб-сайт учета мероприятий', 
                'description': 'Разработка пользовательских сценариев и макетов веб-сайта'
            },
            {
                'id': 3, 
                'icon': 'Component-3.svg', 
                'title': 'Платформа трассировки инженерных сетей', 
                'description': 'Разработка макетов платформы; интеграция базы данных'
            },
            {
                'id': 4, 
                'icon': 'Component-4.svg', 
                'title': 'Платформа для компетенций сотрудников', 
                'description': 'Разработка макетов веб-сайта для главной страницы; разработка ui-kit'
            },
            {
                'id': 5, 
                'icon': 'Component-5.svg', 
                'title': 'Визуальная обучающая игра', 
                'description': 'Отрисовка спрайтов персонажей, разработка динамиечских макетов главного меню'
            },
        ]
    }), name="edit_profile"),
    path("profile/", TemplateView.as_view(template_name="profile.html"), name="profile"),
    path(
    "matrix/",
    TemplateView.as_view(
        template_name="matrix.html",
        extra_context={
            "categories": [
                {
                    "name": "Языки программирования",
                    "skills": ["Java", "Python", "JavaScript", "TypeScript", "SQL"],
                },
                {
                    "name": "Бэкенд",
                    "skills": ["Spring", "Django", "Node.js"],
                },
                {
                    "name": "DevOps",
                    "skills": ["Docker", "Kubernetes", "AWS"],
                },
                {
                    "name": "Методологии",
                    "skills": ["Agile", "Scrum"],
                },
            ],

            "employees": [
                {
                    "name": "Иванов Иван",
                    "role": "Senior Backend Developer",
                    "skills": {
                        "Java": {"level": 4, "confirmed": True},
                        "Python": {"level": 3, "confirmed": False},
                        "JavaScript": {"level": 3, "confirmed": True},
                        "TypeScript": {"level": 3, "confirmed": False},
                        "SQL": {"level": 4, "confirmed": True},
                        "Spring": {"level": 4, "confirmed": True},
                        "Django": {"level": 3, "confirmed": False},
                        "Node.js": {"level": 3, "confirmed": True},
                        "Docker": {"level": 4, "confirmed": True},
                        "Kubernetes": {"level": 4, "confirmed": False},
                        "AWS": {"level": 4, "confirmed": True},
                        "Agile": {"level": 4, "confirmed": True},
                        "Scrum": {"level": 4, "confirmed": False},
                    },
                },

                {
                    "name": "Петрова Анна",
                    "role": "Frontend Developer",
                    "skills": {
                        "Java": {"level": 1, "confirmed": False},
                        "Python": {"level": 2, "confirmed": False},
                        "JavaScript": {"level": 4, "confirmed": True},
                        "TypeScript": {"level": 4, "confirmed": True},
                        "SQL": {"level": 2, "confirmed": False},
                        "Spring": {"level": 0, "confirmed": False},
                        "Django": {"level": 1, "confirmed": False},
                        "Node.js": {"level": 2, "confirmed": False},
                        "Docker": {"level": 3, "confirmed": True},
                        "Kubernetes": {"level": 2, "confirmed": False},
                        "AWS": {"level": 2, "confirmed": False},
                        "Agile": {"level": 4, "confirmed": True},
                        "Scrum": {"level": 4, "confirmed": True},
                    },
                },

                {
                    "name": "Сидоров Алексей",
                    "role": "DevOps Engineer",
                    "skills": {
                        "Java": {"level": 1, "confirmed": False},
                        "Python": {"level": 4, "confirmed": True},
                        "JavaScript": {"level": 2, "confirmed": False},
                        "TypeScript": {"level": 2, "confirmed": False},
                        "SQL": {"level": 2, "confirmed": True},
                        "Spring": {"level": 1, "confirmed": False},
                        "Django": {"level": 2, "confirmed": True},
                        "Node.js": {"level": 3, "confirmed": True},
                        "Docker": {"level": 4, "confirmed": True},
                        "Kubernetes": {"level": 4, "confirmed": True},
                        "AWS": {"level": 4, "confirmed": True},
                        "Agile": {"level": 2, "confirmed": False},
                        "Scrum": {"level": 3, "confirmed": True},
                    },
                },

                {
                    "name": "Кузнецова Мария",
                    "role": "QA Engineer",
                    "skills": {
                        "Java": {"level": 1, "confirmed": False},
                        "Python": {"level": 1, "confirmed": True},
                        "JavaScript": {"level": 0, "confirmed": False},
                        "TypeScript": {"level": 0, "confirmed": False},
                        "SQL": {"level": 2, "confirmed": False},
                        "Spring": {"level": 0, "confirmed": False},
                        "Django": {"level": 1, "confirmed": False},
                        "Node.js": {"level": 1, "confirmed": False},
                        "Docker": {"level": 2, "confirmed": True},
                        "Kubernetes": {"level": 0, "confirmed": False},
                        "AWS": {"level": 0, "confirmed": False},
                        "Agile": {"level": 3, "confirmed": True},
                        "Scrum": {"level": 2, "confirmed": False},
                    },
                },
            ],
        },
    ),
    name="matrix",
),
    path("hr/", TemplateView.as_view(template_name="hr.html"), name="hr"),
    path("ask/", TemplateView.as_view(template_name="ask.html"), name="ask"),
]