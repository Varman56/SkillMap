
## Запуск через docker-compose (запуск команд из корневой папки)

```bash
#1
copy backend\.env.example .env #отредактировать переменные окружения

#2
docker compose up --build #создание контейнеров c пересборкой образов(выполнить для запуска приложения)
docker compose exec backend python manage.py migrate
```

## Тестовое окружение
```bash
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo_data 
```

## Дополнительные команды
```bash
docker compose down -v #остановка и удаление контейнеров и удаление volumes (также очищает бд и применение миграций)
docker compose down #остановка и удаление контейнеров
docker compose up #создание контейнеров без пересборки образов
```
Сайт будет доступен на `http://localhost:5181/...`