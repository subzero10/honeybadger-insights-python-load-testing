# Flask Honeybadger Insights Test App

A Flask web application for testing Honeybadger Insights automatic instrumentation.

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

3. Create database (if it doesn't exist):
```sql
CREATE DATABASE honeybadger_flask_test;
```

4. Start Redis server (for Celery):
```bash
redis-server
```

5. Start Celery worker (in separate terminal):
```bash
celery -A app:celery worker --loglevel=info
```

6. Run Flask application:
```bash
flask --app app run --port 5001 --debug
```

## Endpoints

- `/` - Index page with test interface
- `/api/data/` - JSON endpoint returning database records  
- `/api/task/` - POST endpoint to trigger Celery tasks

## Database

The application will automatically create the required tables on first run.
