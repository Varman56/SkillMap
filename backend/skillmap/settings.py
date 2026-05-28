"""Django settings for skillmap project."""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# NetAngels: переменные окружения хранятся как отдельные файлы в etc/environment/.
# uWSGI там запускается без шелла, поэтому .envrc не выполняется — подгрузим вручную.
# Локально папка не существует, блок просто ничего не делает.
_NETANGELS_ENV = BASE_DIR.parent / "etc" / "environment"
if _NETANGELS_ENV.is_dir():
    for _f in _NETANGELS_ENV.iterdir():
        if _f.is_file() and _f.name.isidentifier():
            try:
                os.environ[_f.name] = _f.read_text().strip()
            except Exception:
                pass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-secret-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,*")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "skillmap.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # spa/index.html — то, что генерирует webpack при сборке фронта.
        # templates/ оставлен как fallback на случай отсутствия собранной SPA.
        "DIRS": [BASE_DIR / "spa", BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "skillmap.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # NetAngels Cloud Hosting автоматически создаёт переменные
        # DBNAME/DBUSER/DBPASS/DBHOST. Берём их как fallback, чтобы не дублировать.
        "NAME": os.getenv("DB_NAME") or os.getenv("DBNAME", "SkillMap"),
        "USER": os.getenv("DB_USER") or os.getenv("DBUSER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD") or os.getenv("DBPASS", "your_password"),
        "HOST": os.getenv("DB_HOST") or os.getenv("DBHOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "api.User"

AUTHENTICATION_BACKENDS = [
    "api.auth_backends.EmailBackend",
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "spa"] if (BASE_DIR / "spa").exists() else []

# WhiteNoise: отдавать собранные SPA-ассеты (bundle.js, картинки, css)
# из backend/spa/ напрямую по корневому пути ('/bundle.js', '/css/...').
# Так index.html со ссылками вида <script src="bundle.js"> работает без правок.
WHITENOISE_ROOT = BASE_DIR / "spa"
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_LIFETIME_MINUTES", "60"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_LIFETIME_DAYS", "7"))
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "api.serializers.SkillMapTokenObtainSerializer",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SkillMap API",
    "DESCRIPTION": "API для платформы SkillMap",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,https://localhost:3000,"
    "http://localhost:5173,https://localhost:5173,"
    "http://localhost:8080,https://localhost:8080",
)
CORS_ALLOW_CREDENTIALS = True

PASSWORD_HASHERS = [
    "api.hashers.BCryptNetHasher",
]

# Яндекс OAuth — заполни в .env, если хочешь включить вход через Яндекс ID.
# Регистрация приложения: https://oauth.yandex.ru → Создать приложение,
# Платформа: «Веб-сервисы», Redirect URI: <твой хост>/api/auth/yandex/callback,
# Права: login:email, login:info.
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET", "")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "")
YANDEX_SUCCESS_REDIRECT = os.getenv(
    "YANDEX_SUCCESS_REDIRECT", "/auth/yandex/success"
)

# Кэш — нужен для одноразовых OAuth ticket'ов и CSRF state'ов.
# FileBasedCache, потому что под uWSGI/Gunicorn несколько worker-процессов,
# и LocMemCache между ними не разделяется (state CSRF теряется).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(BASE_DIR / "tmp_cache"),
    }
}

# Логи ошибок Django — в файл log/django.log (если папка log/ существует).
_LOG_DIR = BASE_DIR.parent / "log"
if _LOG_DIR.is_dir():
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
        },
        "handlers": {
            "file": {
                "level": "ERROR",
                "class": "logging.FileHandler",
                "filename": str(_LOG_DIR / "django.log"),
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django": {"handlers": ["file"], "level": "ERROR", "propagate": True},
            "django.request": {"handlers": ["file"], "level": "ERROR", "propagate": False},
        },
    }
