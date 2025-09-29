#!/bin/bash

# Start Celery worker for Django app
echo "Starting Celery worker for Django app..."

# Make sure we're in the Django app directory
cd "$(dirname "$0")"

# Start the Celery worker
celery -A honeybadger_django worker --loglevel=info