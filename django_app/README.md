# Django Honeybadger Insights Test App

A Django web application for testing Honeybadger Insights automatic instrumentation.

## Features

- Index page with interactive buttons
- JSON API endpoint that returns data from MySQL database
- Celery task endpoint for background job processing

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file and configure:
```bash
cp .env.example .env
```

3. Create database and run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create superuser (optional):
```bash
python manage.py createsuperuser
```

5. Start Redis server (for Celery):
```bash
redis-server
```

6. Start Celery worker (in separate terminal):
```bash
celery -A honeybadger_django worker --loglevel=info
```

7. Run Django development server:
```bash
python manage.py runserver
```

## Endpoints

- `/` - Index page with test interface
- `/api/data/` - JSON endpoint returning database records
- `/api/task/` - POST endpoint to trigger Celery tasks
- `/admin/` - Django admin interface