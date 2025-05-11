# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système si nécessaire
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Pour la production
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]

# Pour le développement (override dans docker-compose)
# command: python manage.py runserver 0.0.0.0:8000