FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

COPY db.sqlite3 /app/db.sqlite3

RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000





RUN python manage.py collectstatic --noinput


CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
