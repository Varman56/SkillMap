#сборка фронтенда
FROM node:24-slim AS frontend-build
WORKDIR /app

COPY skillmap-frontend/package*.json ./skillmap-frontend/
RUN cd skillmap-frontend && npm install

COPY skillmap-frontend/ ./skillmap-frontend/
RUN cd skillmap-frontend && npm run build
# результат: /app/backend/spa/bundle.js и ассеты

#backend
FROM python:3.12-slim AS backend
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /app/backend/spa ./spa

EXPOSE 5181
CMD sh -c "python manage.py migrate && gunicorn skillmap.wsgi:application --bind 0.0.0.0:5181"