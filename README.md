
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