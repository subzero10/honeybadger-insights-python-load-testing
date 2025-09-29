# Honeybadger Insights Python Testing Applications

This repository contains two Python web applications (Django and Flask) designed to test the Honeybadger Insights automatic instrumentation features.

## Applications

### Django App
- **Location**: `django_app/`
- **Port**: 8000 (default Django port)
- **Features**: Index page, JSON API endpoint, Celery task endpoint
- **Admin Interface**: `/admin/` (after creating superuser)

### Flask App
- **Location**: `flask_app/`
- **Port**: 5000 (default Flask port)
- **Features**: Index page, JSON API endpoint, Celery task endpoint

## Prerequisites

- Python 3.8+
- MySQL 8.0+
- Redis 6.0+
- Docker and Docker Compose (optional, for easy setup)

## Quick Start with Docker

1. Start MySQL and Redis services:
```bash
docker-compose up -d
```

2. Set up Django application:
```bash
cd django_app
cp .env.example .env
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # optional
```

3. Set up Flask application:
```bash
cd ../flask_app
cp .env.example .env
pip install -r requirements.txt
```

4. Start Celery workers (in separate terminals):
```bash
# For Django (from django_app directory)
./start_celery.sh

# For Flask (from flask_app directory)  
./start_celery.sh
```

5. Start the applications:
```bash
# Django (from django_app directory)
python manage.py runserver

# Flask (from flask_app directory)
flask --app app run --port 5000 --debug
```

## Manual Setup

If you prefer to set up MySQL and Redis manually:

1. Create databases:
```bash
mysql -u root -p < setup_databases.sql
```

2. Start Redis:
```bash
redis-server
```

3. Follow steps 2-5 from the Docker setup above.

## Testing Endpoints

Both applications provide the same endpoints:

- `/` - Interactive index page with test buttons
- `/api/data/` - GET endpoint returning JSON data from MySQL
- `/api/task/` - POST endpoint to trigger Celery background tasks

### Example API Usage

Get data from database:
```bash
curl http://localhost:8000/api/data/  # Django
curl http://localhost:5000/api/data/  # Flask
```

Trigger a Celery task:
```bash
curl -X POST http://localhost:8000/api/task/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "test_task"}'

curl -X POST http://localhost:5000/api/task/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "test_task"}'
```

## Environment Variables

Both applications use the same environment variables:

- `DB_NAME` - Database name
- `DB_USER` - Database username  
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 3306)
- `CELERY_BROKER_URL` - Celery broker URL (default: redis://localhost:6379/0)
- `CELERY_RESULT_BACKEND` - Celery result backend (default: redis://localhost:6379/0)
- `SECRET_KEY` - Application secret key

## Honeybadger Insights Integration

These applications are ready for Honeybadger Insights integration. The automatic instrumentation should capture:

- HTTP requests and responses
- Database queries (MySQL)
- Background task execution (Celery)
- Error tracking and performance monitoring

## Troubleshooting

1. **Database connection errors**: Ensure MySQL is running and credentials are correct
2. **Celery tasks not executing**: Ensure Redis is running and Celery workers are started
3. **Port conflicts**: Change ports in application configurations if needed
