FROM python:3.13-slim

# Установка только реально существующих пакетов
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка Python пакетов
RUN pip install --no-cache-dir \
    Django==5.1.7 \
    django-environ==0.12.0 \
    djangorestframework==3.15.2 \
    djangorestframework-gis==1.0 \
    django-cors-headers==4.7.0 \
    django-filter==25.1 \
    gunicorn==23.0.0 \
    django-extensions==3.2.3 \
    psycopg2-binary==2.9.10 \
    Pillow==11.2.1 \
    django-tinymce==4.1.0 \
    pandas==2.3.0 \
    openpyxl==3.1.5 \
    xlrd==2.0.2 \
    redis==5.1.0 \
    celery==5.4.0 \
    django-redis==5.4.0 \
    drf-spectacular==0.28.0

WORKDIR /app
COPY . .

# Создание пользователя и директорий
RUN mkdir -p /app/staticfiles /app/media && \
    useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod -R 755 /app

USER app

EXPOSE 8000
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]