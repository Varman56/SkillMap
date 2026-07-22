## Стек
- Python 3.11+
- Django 5.1 + Django REST Framework
- `djangorestframework-simplejwt` — JWT (access + refresh)
- PostgreSQL через `psycopg[binary]` 3.x
- `bcrypt` 4.x — совместим с C# BCrypt.Net хешами (`$2a$12$...`)
- `drf-spectacular` — OpenAPI/Swagger
- `whitenoise` — раздача статики SPA
- `django-cors-headers`

## Структура

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── skillmap/              # Django project (settings, urls, wsgi, asgi)
├── api/                   # Один app с моделями + всеми endpoints
│   ├── models.py          # User, Skill, UserSkill, Project, UserProject
│   ├── hashers.py         # BCrypt-совместимый с BCrypt.Net хешер
│   ├── auth_backends.py   # Login по email
│   ├── permissions.py     # IsHR, IsHROrManager
│   ├── serializers.py
│   ├── views/
│   │   ├── auth.py           # /api/auth/login, /logout, /me, /refresh
│   │   ├── users.py          # /api/users (HR)
│   │   ├── skills.py         # /api/skills, /api/skills/my/...
│   │   ├── me.py             # /api/me/dashboard, /api/me/skills
│   │   ├── matrix.py         # /api/matrix (HR/Manager)
│   │   ├── projects.py       # /api/projects/...
│   │   ├── public_profiles.py # /api/public-profiles/{publicId}
│   │   └── ask.py            # /api/ask?skill=...
│   ├── migrations/0001_initial.py  # marker, managed=False — БД не трогает
│   └── urls.py
├── templates/index.html   # SPA точка входа (fallback на все не-API маршруты)
└── spa/                   # собранные ассеты SPA (bundle.js, css, картинки)
```

## API endpoints 
| Method | Route | Доступ |
|---|---|---|
| AuthController.Login | `POST /api/auth/login` | все |
| AuthController.Logout | `POST /api/auth/logout` | auth |
| AuthController.Me | `GET /api/auth/me` | auth |
| — (новый) | `POST /api/auth/refresh` | refresh-токен |
| UsersController.GetUsers | `GET /api/users` | HR |
| UsersController.CreateUser | `POST /api/users` | HR |
| UsersController.GetUserByPublicId | `GET /api/users/{publicId}` | HR |
| ApiSkillsController.GetAvailableSkills | `GET /api/skills/available` | auth |
| ApiSkillsController.GetAllSkills | `GET /api/skills` | auth |
| ApiSkillsController.CreateSkill | `POST /api/skills` | HR |
| ApiSkillsController.AddSkillToCurrentUser | `POST /api/skills/my` | auth |
| ApiSkillsController.RemoveSkillFromCurrentUser | `DELETE /api/skills/my/{skillId}` | auth |
| ApiSkillsController.UpdateCurrentUserSkillLevel | `PATCH /api/skills/my/{skillId}/level` | auth |
| MeController.GetDashboard | `GET /api/me/dashboard?search=...` | auth |
| MeController.GetMySkills | `GET /api/me/skills?search=...` | auth |
| MatrixController.GetMatrix | `GET /api/matrix` | HR/Manager |
| ProjectsController.GetAll | `GET /api/projects` | auth |
| ProjectsController.GetById | `GET /api/projects/{id}` | auth |
| ProjectsController.Create | `POST /api/projects` | HR/Manager |
| ProjectsController.Update | `PUT /api/projects/{id}` | HR/Manager |
| ProjectsController.Delete | `DELETE /api/projects/{id}` | HR/Manager |
| ProjectsController.AddMember | `POST /api/projects/{id}/members` | HR/Manager |
| ProjectsController.RemoveMember | `DELETE /api/projects/{id}/members/{publicId}` | HR/Manager |
| PublicProfilesController.GetProfile | `GET /api/public-profiles/{publicId}` | auth |
| AskController.SearchBySkill | `GET /api/ask?skill=...` | auth |


## Запуск через docker-compose (запуск команд из корневой папки)

```bash
#1
copy backend\.env.example .env #отредактировать переменные окружения

#2
docker compose up --build #создание контейнеров c пересборкой образов(выполнить для запуска приложения)

#3
docker compose exec backend python manage.py seed_demo_data #запустить в терминале для заполнения тестовых данных

#дополнительные команды
docker compose down -v #остановка и удаление контейнеров и удаление volumes
docker compose down #остановка и удаление контейнеров
docker compose up #создание контейнеров без пересборки образов
```
API будет доступен на `http://localhost:5181/api/...`, фронт — на `http://localhost:5181/`.
Swagger UI: `GET /api/docs/`

## Запуск бэкэнда
API на `http://localhost:5181/api/...`
```bash
#1
python -m venv backend/.venv
.\backend\.venv\Scripts\activate
pip install -r backend/requirements.txt

#2
copy backend/.env.example backend/.env               # потом отредактируй пароль БД и SECRET_KEY

#3
docker compose up -d db #запуск базы данных

#для заполнения базы данными выполнить
python backend/manage.py migrate 
python backend/manage.py seed_demo_data

#для запуска сервера выполнить
python backend/manage.py runserver 0.0.0.0:5181
```

## Запуск фронтенда в отдельном контейнере(должен быть запущен бэк)
фронт будет на - `http://localhost:8080/`
```bash
#1
cd skillmap-frontend

#2
docker run -it --rm -v ${PWD}:/app -w /app -p 8080:8080 node:24-slim sh #запуск контейнера Node.js для Windows
docker run -it --rm --network host -v ${PWD}:/app -w /app node:24-slim sh #запуск контейнера Node.js для Linux

# далее внутри контейнера выполнить
#1
npm install
#2
npm run dev
```

## Изменения для фронтенда (cookie → JWT)
Старый бэкенд возвращал `Set-Cookie` после `/api/auth/login` и
проверял cookies на каждом запросе.

Новый бэкенд возвращает JSON:

```json
{
  "success": true,
  "user": { ... },
  "tokens": {
    "access":  "eyJhbGciOi...",
    "refresh": "eyJhbGciOi..."
  }
}
```

Фронту нужно:

1. Сохранить `access` (например в `localStorage`) и слать его в заголовке
   `Authorization: Bearer <access>` на каждый запрос к `/api/...`.
2. Когда сервер возвращает `401`, дергать `POST /api/auth/refresh`
   с телом `{"refresh": "..."}`, получить новый `access`.
3. На logout: вызвать `POST /api/auth/logout` с телом `{"refresh": "..."}`
   (опционально, для blacklist) и удалить токены из хранилища.

