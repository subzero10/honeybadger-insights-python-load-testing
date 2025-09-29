#!/bin/bash

# Start Celery worker for Flask app
echo "Starting Celery worker for Flask app..."

# Make sure we're in the Flask app directory
cd "$(dirname "$0")"

# Start the Celery worker with proper module import
celery -A app:celery worker --loglevel=info