# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Honeybadger Insights testing repository containing two Python web applications (Django and Flask) and a comprehensive load testing framework designed to test automatic instrumentation features and performance impact. Both applications provide identical endpoints and functionality for comprehensive testing.

## Architecture

### Three Main Components
- **Django App** (`django_app/`): Standard Django project with Celery integration
  - Main project: `honeybadger_django/`
  - App: `testapp/` (contains models, views, tasks)
  - Port: 8000
- **Flask App** (`flask_app/`): Single-file Flask application with SQLAlchemy and Celery
  - Main file: `app.py`
  - Port: 5000
- **Load Testing App** (`load_testing/`): Comprehensive performance testing framework
  - Uses Locust for load generation
  - Compares performance with/without Honeybadger Insights
  - Monitors system resources and generates reports

### Key Components
- **Database**: MySQL (separate databases for each app)
- **Task Queue**: Celery with Redis backend
- **Models**: `TestData` model for storing test records
- **API Endpoints**: 
  - `/` - Interactive test interface
  - `/api/data/` - Returns database records as JSON
  - `/api/task/` - Triggers background Celery tasks
  - `/api/error/` - Triggers a ZeroDivisionError
  - 

## Development Commands

### Initial Setup
```bash
# Start infrastructure services
docker-compose up -d

# Setup Django
cd django_app
cp .env.example .env
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # optional

# Setup Flask
cd ../flask_app
cp .env.example .env
pip install -r requirements.txt

# Setup load testing
cd load_testing
pip install -r requirements.txt
```

### Running Applications
```bash
# Django
cd django_app
python manage.py runserver                 # Starts on port 8000

# Flask
cd flask_app
flask --app app run --port 5000 --debug    # Starts on port 5000
```

### Running Load Tests
```bash
cd load_testing

# Run comparison tests (both apps with/without Insights)
python test_runner.py ..                    # Default light load test
python test_runner.py .. medium_load        # Medium load test
python test_runner.py .. heavy_load django  # Heavy load on Django only

# Generate performance reports
python report_generator.py results/django_medium_load_comparison_20231201_143022.json

# Monitor system resources only
python resource_monitor.py
```

### Running Celery Workers
```bash
# Django (from django_app directory)
./start_celery.sh
# or manually: celery -A honeybadger_django worker --loglevel=info

# Flask (from flask_app directory)
./start_celery.sh
# or manually: celery -A app:celery worker --loglevel=info
```

### Database Management
```bash
# Setup databases manually (if not using Docker)
mysql -u root -p < setup_databases.sql

# Django migrations
cd django_app
python manage.py makemigrations
python manage.py migrate

# Flask automatically creates tables on first run
```

## Environment Configuration

Both applications use identical environment variables (see `.env.example` files):
- `DB_NAME` - Database name (different for each app)
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database connection
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Redis configuration
- `SECRET_KEY` - Application secret key
- `HONEYBADGER_API_KEY` - Honeybadger API Key
- `HONEYBADGER_INSIGHTS_ENABLED` - Enable or disable Honeybadger Insights

## Testing the Applications

Both apps expose identical functionality:
- Visit `/` for interactive testing interface
- `GET /api/data/` - Retrieve all test data from database
- `POST /api/task/` - Trigger background task (creates new database record)
- `POST /api/error/` - Trigger a ZeroDivision error (to test error reporting to Honeybadger)
- `GET /api/warmup/` - Pre-initialize Honeybadger Insights components (performance optimization)

Use curl examples from main README.md to test API endpoints.

## Dependencies

### Django App
- Django 4.2.7, PyMySQL, Celery 5.3.4, Redis, python-dotenv

### Flask App  
- Flask 3.0.0, SQLAlchemy 2.0.23, Flask-SQLAlchemy, PyMySQL, Celery 5.3.4, Redis, python-dotenv

### Load Testing App
- Locust 2.16.1, psutil 5.9.0, requests 2.31.0, pandas 2.0.0, matplotlib 3.7.0, seaborn 0.12.0

## Performance Optimizations

Both Django and Flask applications have been optimized to reduce Honeybadger Insights cold start latency:

### Eager Initialization
- **Django**: WSGI application pre-initializes Honeybadger during startup (`wsgi.py`)
- **Flask**: Application startup includes Insights component warmup (`app.py`)
- **Configuration**: Optimized async reporting, batching, and timeout settings

### Warmup Endpoints
- `/api/warmup/` endpoint available in both applications
- Pre-initializes database connections and Insights monitoring
- Can be used by load balancers and health checks
- Returns status of initialization components

### Load Testing Enhancements
- Automatic warmup before test execution
- Individual user warmup for realistic scenarios
- Performance tracking for cold vs warm requests

### Performance Validation
Test the performance improvements using the provided test script:
```bash
# Start both applications with Insights enabled
cd django_app && python manage.py runserver &
cd flask_app && flask --app app run --port 5000 &

# Run performance validation
python test_performance_improvements.py

# Expected results: First request latency < 200ms (down from 500-1000ms)
```

## Load Testing Framework

The load testing framework provides comprehensive performance comparison between Django and Flask applications with and without Honeybadger Insights instrumentation enabled.

### Test Configurations
- **light_load**: 10 users, 2 spawn rate, 2 minutes
- **medium_load**: 50 users, 5 spawn rate, 5 minutes  
- **heavy_load**: 100 users, 10 spawn rate, 5 minutes
- **burst_load**: 200 users, 50 spawn rate, 3 minutes

### User Behavior Patterns
- **WebAppUser**: Realistic mixed workload (40% homepage, 30% API data, 20% tasks, 10% errors)
- **HeavyUser**: Intensive operations with minimal wait time
- **BurstUser**: Creates burst traffic patterns
- **DatabaseHeavyUser**: Focuses on database operations

### Key Components
- **locustfile.py**: Load test scenarios and user behaviors
- **test_runner.py**: Main test orchestration script
- **resource_monitor.py**: System resource monitoring
- **report_generator.py**: Performance analysis and reporting
- **env_configs/**: Environment configurations for enabling/disabling Insights

### What Gets Measured
- **Application Performance**: Request throughput, response times, error rates
- **System Resources**: CPU usage, memory consumption, thread count, file descriptors
- **Comparison Metrics**: Performance overhead, resource usage differences, stability

### Output Files
- **CSV files**: Locust raw data with detailed request-level statistics
- **HTML reports**: Interactive Locust performance dashboards
- **JSON files**: Resource monitoring data and comparison results
- **Markdown reports**: Human-readable performance analysis
- **PNG charts**: Visual performance comparison graphs

## File Structure Notes

- Django follows standard Django project structure with separate app (`testapp`)
- Flask is a single-file application (`app.py`) with templates in `templates/`
- Both have convenience scripts (`start_celery.sh`) for running Celery workers
- Load testing framework (`load_testing/`) contains Locust-based performance testing suite
- Database setup script (`setup_databases.sql`) creates both required databases
