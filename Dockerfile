# Corporate Dining System — production Dockerfile
FROM python:3.12-slim

# Python баптаулары
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Жүйелік тәуелділіктер (psycopg үшін)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python тәуелділіктерін орнату (кэштеу үшін бөлек қабат)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Жоба файлдарын көшіру
COPY . .

# Статикалық файлдарды жинау (DEBUG/DB қажет емес, build-кезінде орындалады)
RUN SECRET_KEY=build-only DEBUG=False ALLOWED_HOSTS=* \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Контейнер іске қосылғанда: миграция + gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn dining_system.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3"]
