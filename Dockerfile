#backend
FROM python:3.12-slim AS backend
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 5181
CMD sh -c "python manage.py migrate && gunicorn --workers 2 --threads 2 --keep-alive 0 --timeout 30 \
  --access-logfile - --access-logformat '%(t)s %(r)s %(s)s %(D)s' \
  skillmap.wsgi:application --bind 0.0.0.0:5181"